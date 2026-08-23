import asyncio
import hashlib
import json
from collections.abc import Iterator
from typing import Any

import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base, load_models
from app.models.data_source import DataSource
from app.models.ingestion_run import IngestionRun
from app.models.job_posting import JobPosting
from app.models.raw_source_record import RawSourceRecord
from app.services.ingestion_service import IngestionService


@compiles(JSONB, "sqlite")
def compile_jsonb_for_sqlite(type_: JSONB, compiler: Any, **kwargs: Any) -> str:
    return "JSON"


class FakeMuseClient:
    """Test double for the synchronous Muse client"""

    def __init__(self, response: dict[str, Any] | Exception) -> None:
        self.response = response

    def fetch_jobs(self) -> dict[str, Any]:
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


class FakeRemotiveClient:
    """Test double for the asynchronous Remotive client"""

    def __init__(self, response: dict[str, Any] | Exception) -> None:
        self.response = response

    async def fetch_jobs(self) -> dict[str, Any]:
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


@pytest.fixture
def session() -> Iterator[Session]:
    load_models()
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection: Any, connection_record: Any) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    database_session = sessionmaker(bind=engine)()
    yield database_session
    database_session.close()
    Base.metadata.drop_all(engine)
    engine.dispose()


def muse_response(title: str = "Python Developer") -> dict[str, Any]:
    return {
        "results": [
            {
                "id": 123,
                "name": title,
                "refs": {"landing_page": "https://muse.test/jobs/123"},
                "company": {"name": "Muse Company"},
                "publication_date": "2026-08-21T10:00:00Z",
                "locations": [{"name": "Flexible / Remote"}],
                "categories": [{"name": "Software Engineering"}],
                "type": "external",
                "contents": "<p>Build&nbsp;<strong>APIs</strong></p>",
            }
        ]
    }


def remotive_response() -> dict[str, Any]:
    return {
        "jobs": [
            {
                "id": 456,
                "url": "https://remotive.test/jobs/456",
                "title": "Remote Python Developer",
                "company_name": "Remotive Company",
                "publication_date": "2026-08-21T10:00:00",
                "candidate_required_location": "Worldwide",
                "category": "Software Development",
                "job_type": "full_time",
                "description": "<div>Build <em>remote</em> systems</div>",
            }
        ]
    }


def create_source(session: Session, code: str) -> DataSource:
    source = DataSource(name=code.title(), code=code, base_url=f"https://{code}.test")
    session.add(source)
    session.commit()
    return source


def test_muse_ingestion_creates_run_snapshot_and_posting(session: Session) -> None:
    source = create_source(session, "muse")
    service = IngestionService(
        session,
        FakeMuseClient(muse_response()),
        FakeRemotiveClient(remotive_response()),
    )

    run = asyncio.run(service.ingest(source))

    assert run.status == "success"
    assert run.records_received == 1
    assert session.scalars(select(RawSourceRecord)).all()[0].external_id == "123"
    posting = session.scalars(select(JobPosting)).one()
    assert posting.title == "Python Developer"
    assert posting.description_text == "Build APIs"
    assert posting.is_active is True
    assert source.last_successful_sync_at is not None


def test_remotive_ingestion_creates_run_snapshot_and_posting(session: Session) -> None:
    source = create_source(session, "remotive")
    service = IngestionService(
        session,
        FakeMuseClient(muse_response()),
        FakeRemotiveClient(remotive_response()),
    )

    run = asyncio.run(service.ingest(source))

    assert run.status == "success"
    assert session.scalars(select(RawSourceRecord)).all()[0].external_id == "456"
    posting = session.scalars(select(JobPosting)).one()
    assert posting.is_remote is True
    assert posting.location_scope == "Worldwide"


def test_second_ingestion_creates_snapshot_and_updates_existing_posting(
    session: Session,
) -> None:
    source = create_source(session, "muse")
    service = IngestionService(
        session,
        FakeMuseClient(muse_response()),
        FakeRemotiveClient(remotive_response()),
    )
    asyncio.run(service.ingest(source))
    posting = session.scalars(select(JobPosting)).one()
    first_seen_at = posting.first_seen_at
    first_last_seen_at = posting.last_seen_at

    service._muse_client = FakeMuseClient(
        muse_response(title="Senior Python Developer")
    )
    asyncio.run(service.ingest(source))

    snapshots = session.scalars(
        select(RawSourceRecord).order_by(RawSourceRecord.id)
    ).all()
    updated_posting = session.scalars(select(JobPosting)).one()
    assert len(snapshots) == 2
    assert len(session.scalars(select(JobPosting)).all()) == 1
    assert updated_posting.title == "Senior Python Developer"
    assert updated_posting.first_seen_at == first_seen_at
    assert updated_posting.last_seen_at > first_last_seen_at


def test_payload_hash_is_deterministic(session: Session) -> None:
    source = create_source(session, "muse")
    payload = muse_response()["results"][0]
    service = IngestionService(
        session,
        FakeMuseClient({"results": [payload]}),
        FakeRemotiveClient(remotive_response()),
    )

    asyncio.run(service.ingest(source))

    expected_hash = hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()
    assert session.scalars(select(RawSourceRecord)).one().payload_hash == expected_hash


def test_client_failure_marks_run_failed_and_reraises(session: Session) -> None:
    source = create_source(session, "muse")
    service = IngestionService(
        session,
        FakeMuseClient(RuntimeError("Muse unavailable")),
        FakeRemotiveClient(remotive_response()),
    )

    with pytest.raises(RuntimeError, match="Muse unavailable"):
        asyncio.run(service.ingest(source))

    run = session.scalars(select(IngestionRun)).one()
    assert run.status == "failed"
    assert run.finished_at is not None
    assert run.error_message == "Muse unavailable"


def test_html_to_text_is_deterministic() -> None:
    assert IngestionService._html_to_text(
        "<p>Python&nbsp;developer</p><p>Build APIs</p>"
    ) == ("Python developer Build APIs")
