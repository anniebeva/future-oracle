import asyncio
import hashlib
import json
from datetime import UTC, datetime
from html.parser import HTMLParser
from typing import Any, Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.data_source import DataSource
from app.models.ingestion_run import IngestionRun
from app.models.job_posting import JobPosting
from app.models.raw_source_record import RawSourceRecord


class _HTMLTextExtractor(HTMLParser):
    """Collect text content from HTML"""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"br", "p", "div", "li"}:
            self.parts.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"p", "div", "li"}:
            self.parts.append(" ")

    def text(self) -> str:
        """Return normalized collected text"""
        return " ".join("".join(self.parts).split())


class MuseJobsClient(Protocol):
    """Minimal interface required from the Muse client"""

    def fetch_jobs(self) -> dict[str, Any]: ...


class RemotiveJobsClient(Protocol):
    """Minimal interface required from the Remotive client"""

    async def fetch_jobs(self) -> dict[str, Any]: ...


class IngestionService:
    """Persist raw snapshots and canonical job postings"""

    def __init__(
        self,
        session: Session,
        muse_client: MuseJobsClient,
        remotive_client: RemotiveJobsClient,
    ) -> None:
        self._session = session
        self._muse_client = muse_client
        self._remotive_client = remotive_client

    async def ingest(self, source: DataSource) -> IngestionRun:
        """Collect and persist jobs for one configured source"""
        if source.id is None:
            raise ValueError("DataSource must be persisted before ingestion")

        run = IngestionRun(source_id=source.id, status="running")
        self._session.add(run)
        self._session.commit()

        try:
            response = await self._fetch_source_jobs(source.code)
            jobs = self._jobs_from_response(source.code, response)
            retrieved_at = datetime.now(UTC)

            for job in jobs:
                normalized = self._normalize_job(source.code, job)
                external_id = normalized["external_id"]
                payload_hash = self._payload_hash(job)
                self._session.add(
                    RawSourceRecord(
                        ingestion_run_id=run.id,
                        source_id=source.id,
                        external_id=external_id,
                        retrieved_at=retrieved_at,
                        payload=job,
                        payload_hash=payload_hash,
                    )
                )
                self._upsert_job_posting(source.id, normalized, retrieved_at)

            completed_at = datetime.now(UTC)
            run.status = "success"
            run.finished_at = completed_at
            run.records_received = len(jobs)
            source.last_successful_sync_at = completed_at
            self._session.commit()
        except Exception as error:
            self._session.rollback()
            run.status = "failed"
            run.finished_at = datetime.now(UTC)
            run.error_message = str(error)
            self._session.commit()
            raise

        return run

    async def _fetch_source_jobs(self, source_code: str) -> dict[str, Any]:
        if source_code == "muse":
            return await asyncio.to_thread(self._muse_client.fetch_jobs)
        if source_code == "remotive":
            return await self._remotive_client.fetch_jobs()
        raise ValueError(f"Unsupported data source: {source_code}")

    def _jobs_from_response(
        self,
        source_code: str,
        response: dict[str, Any],
    ) -> list[dict[str, Any]]:
        key = "results" if source_code == "muse" else "jobs"
        jobs = response.get(key)
        if not isinstance(jobs, list) or not all(isinstance(job, dict) for job in jobs):
            raise ValueError(f"Invalid {source_code} jobs response")
        return jobs

    def _normalize_job(self, source_code: str, job: dict[str, Any]) -> dict[str, Any]:
        if source_code == "muse":
            return self._normalize_muse_job(job)
        if source_code == "remotive":
            return self._normalize_remotive_job(job)
        raise ValueError(f"Unsupported data source: {source_code}")

    def _normalize_muse_job(self, job: dict[str, Any]) -> dict[str, Any]:
        locations = self._named_values(job.get("locations"))
        description_html = self._required_string(job, "contents")
        return {
            "external_id": str(job["id"]),
            "source_url": self._required_nested_string(job, "refs", "landing_page"),
            "title": self._required_string(job, "name"),
            "company_name": self._optional_nested_string(job, "company", "name"),
            "published_at": self._required_datetime(job, "publication_date"),
            "location_raw": ", ".join(locations) if locations else None,
            "location_scope": None,
            "is_remote": any("remote" in location.casefold() for location in locations),
            "category": self._first_named_value(job.get("categories")),
            "employment_type": self._optional_string(job, "type"),
            "description_html": description_html,
            "description_text": self._html_to_text(description_html),
            "content_hash": self._payload_hash(job),
            "is_active": True,
        }

    def _normalize_remotive_job(self, job: dict[str, Any]) -> dict[str, Any]:
        description_html = self._required_string(job, "description")
        return {
            "external_id": str(job["id"]),
            "source_url": self._required_string(job, "url"),
            "title": self._required_string(job, "title"),
            "company_name": self._optional_string(job, "company_name"),
            "published_at": self._required_datetime(job, "publication_date"),
            "location_raw": self._optional_string(job, "candidate_required_location"),
            "location_scope": self._optional_string(job, "candidate_required_location"),
            "is_remote": True,
            "category": self._optional_string(job, "category"),
            "employment_type": self._optional_string(job, "job_type"),
            "description_html": description_html,
            "description_text": self._html_to_text(description_html),
            "content_hash": self._payload_hash(job),
            "is_active": True,
        }

    def _upsert_job_posting(
        self,
        source_id: int,
        normalized: dict[str, Any],
        seen_at: datetime,
    ) -> None:
        posting = self._session.scalar(
            select(JobPosting).where(
                JobPosting.source_id == source_id,
                JobPosting.external_id == normalized["external_id"],
            )
        )
        if posting is None:
            self._session.add(
                JobPosting(
                    source_id=source_id,
                    first_seen_at=seen_at,
                    last_seen_at=seen_at,
                    **normalized,
                )
            )
            return

        for field, value in normalized.items():
            setattr(posting, field, value)
        posting.last_seen_at = seen_at

    @staticmethod
    def _payload_hash(payload: dict[str, Any]) -> str:
        canonical_payload = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()

    @staticmethod
    def _html_to_text(html: str) -> str:
        parser = _HTMLTextExtractor()
        parser.feed(html)
        parser.close()
        return parser.text()

    @staticmethod
    def _named_values(value: object) -> list[str]:
        if not isinstance(value, list):
            return []
        return [
            item["name"]
            for item in value
            if isinstance(item, dict) and isinstance(item.get("name"), str)
        ]

    def _first_named_value(self, value: object) -> str | None:
        values = self._named_values(value)
        return values[0] if values else None

    @staticmethod
    def _required_string(job: dict[str, Any], key: str) -> str:
        value = job.get(key)
        if not isinstance(value, str) or not value:
            raise ValueError(f"Source job is missing {key}")
        return value

    def _required_nested_string(
        self, job: dict[str, Any], parent: str, key: str
    ) -> str:
        value = job.get(parent)
        if not isinstance(value, dict):
            raise ValueError(f"Source job is missing {parent}.{key}")
        return self._required_string(value, key)

    @staticmethod
    def _optional_string(job: dict[str, Any], key: str) -> str | None:
        value = job.get(key)
        return value if isinstance(value, str) else None

    def _optional_nested_string(
        self, job: dict[str, Any], parent: str, key: str
    ) -> str | None:
        value = job.get(parent)
        return self._optional_string(value, key) if isinstance(value, dict) else None

    def _required_datetime(self, job: dict[str, Any], key: str) -> datetime:
        value = self._required_string(job, key)
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as error:
            raise ValueError(f"Source job has invalid {key}") from error
