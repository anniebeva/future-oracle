from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base, load_models
from app.db.session import get_db_session
from app.main import app
from app.models.data_source import DataSource
from app.models.job_posting import JobPosting
from app.models.job_skill_match import JobSkillMatch
from app.models.skill import Skill

PUBLISHED_AT = datetime(2026, 8, 10, 12, tzinfo=UTC)


@compiles(JSONB, "sqlite")
def compile_jsonb_for_sqlite(type_: JSONB, compiler: Any, **kwargs: Any) -> str:
    return "JSON"


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


@pytest.fixture
def client(session: Session) -> Iterator[TestClient]:
    app.dependency_overrides[get_db_session] = lambda: session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def create_source(session: Session, code: str, *, is_active: bool = True) -> DataSource:
    source = DataSource(
        code=code,
        name=code.title(),
        base_url=f"https://{code}.example",
        is_active=is_active,
    )
    session.add(source)
    session.flush()
    return source


def create_skill(
    session: Session,
    code: str = "python",
    *,
    dictionary_version: int = 1,
    is_active: bool = True,
) -> Skill:
    skill = Skill(
        code=code,
        display_name=code.title(),
        dictionary_version=dictionary_version,
        is_active=is_active,
    )
    session.add(skill)
    session.flush()
    return skill


def create_job(
    session: Session,
    source: DataSource,
    external_id: str,
    *,
    title: str = "Python Developer",
    published_at: datetime = PUBLISHED_AT,
    location_raw: str | None = "Berlin, Germany",
    location_scope: str | None = "Europe",
    is_remote: bool = True,
    is_active: bool = True,
) -> JobPosting:
    job = JobPosting(
        source_id=source.id,
        external_id=external_id,
        source_url=f"https://{source.code}.example/{external_id}",
        title=title,
        company_name="Example Company",
        published_at=published_at,
        location_raw=location_raw,
        location_scope=location_scope,
        is_remote=is_remote,
        category="Software Engineering",
        employment_type="full_time",
        description_text="Build Python services",
        content_hash=external_id.zfill(64),
        is_active=is_active,
    )
    session.add(job)
    session.flush()
    return job


def create_match(
    session: Session,
    job: JobPosting,
    skill: Skill,
    *,
    dictionary_version: int = 1,
) -> None:
    session.add(
        JobSkillMatch(
            job_posting_id=job.id,
            skill_id=skill.id,
            dictionary_version=dictionary_version,
            matched_alias=skill.code,
            matched_in_title=True,
            matched_in_description=False,
            match_count=1,
        )
    )
    session.flush()


def test_endpoint_returns_only_active_jobs_from_active_sources(
    client: TestClient, session: Session
) -> None:
    active_source = create_source(session, "muse")
    inactive_source = create_source(session, "remotive", is_active=False)
    active_job = create_job(session, active_source, "1")
    create_job(session, active_source, "2", is_active=False)
    create_job(session, inactive_source, "1")
    session.commit()

    response = client.get("/api/jobs")

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [active_job.id]


def test_source_and_skill_filters_work_without_duplicate_jobs(
    client: TestClient, session: Session
) -> None:
    muse = create_source(session, "muse")
    remotive = create_source(session, "remotive")
    python = create_skill(session, "python")
    docker = create_skill(session, "docker")
    python_job = create_job(session, muse, "1")
    docker_job = create_job(session, remotive, "1")
    create_match(session, python_job, python)
    create_match(session, python_job, python, dictionary_version=0)
    create_match(session, docker_job, docker)
    session.commit()

    source_response = client.get("/api/jobs", params={"source": "muse"})
    skill_response = client.get("/api/jobs", params={"skill": "python"})

    assert [item["id"] for item in source_response.json()] == [python_job.id]
    assert [item["id"] for item in skill_response.json()] == [python_job.id]


def test_current_dictionary_version_is_respected(
    client: TestClient, session: Session
) -> None:
    source = create_source(session, "muse")
    python = create_skill(session, "python", dictionary_version=2)
    old_match_job = create_job(session, source, "1")
    current_match_job = create_job(session, source, "2")
    create_match(session, old_match_job, python, dictionary_version=1)
    create_match(session, current_match_job, python, dictionary_version=2)
    session.commit()

    response = client.get("/api/jobs", params={"skill": "python"})

    assert [item["id"] for item in response.json()] == [current_match_job.id]
    assert response.json()[0]["skills"] == [
        {"code": "python", "display_name": "Python"}
    ]


def test_location_remote_and_title_search_filters_work(
    client: TestClient, session: Session
) -> None:
    source = create_source(session, "muse")
    berlin_remote = create_job(session, source, "1", title="Backend Python Engineer")
    create_job(
        session,
        source,
        "2",
        title="Frontend Engineer",
        location_raw="New York, USA",
        location_scope="North America",
        is_remote=False,
    )
    session.commit()

    response = client.get(
        "/api/jobs",
        params={"location": "berlin", "is_remote": "true", "search": "PYTHON"},
    )

    assert [item["id"] for item in response.json()] == [berlin_remote.id]


def test_publication_filters_and_combined_filters_work(
    client: TestClient, session: Session
) -> None:
    muse = create_source(session, "muse")
    remotive = create_source(session, "remotive")
    python = create_skill(session, "python")
    older_published_at = PUBLISHED_AT - timedelta(days=1)
    older = create_job(session, muse, "1", published_at=older_published_at)
    current = create_job(session, muse, "2")
    remotive_current = create_job(session, remotive, "1")
    create_match(session, current, python)
    session.commit()

    from_response = client.get(
        "/api/jobs", params={"published_from": PUBLISHED_AT.isoformat()}
    )
    to_response = client.get(
        "/api/jobs", params={"published_to": older_published_at.isoformat()}
    )
    combined_response = client.get(
        "/api/jobs",
        params={
            "source": "muse",
            "skill": "python",
            "published_from": PUBLISHED_AT.isoformat(),
            "published_to": PUBLISHED_AT.isoformat(),
        },
    )

    assert {item["id"] for item in from_response.json()} == {
        current.id,
        remotive_current.id,
    }
    assert [item["id"] for item in to_response.json()] == [older.id]
    assert [item["id"] for item in combined_response.json()] == [current.id]


def test_results_are_ordered_by_newest_publication_then_id(
    client: TestClient, session: Session
) -> None:
    source = create_source(session, "muse")
    older = create_job(
        session, source, "1", published_at=PUBLISHED_AT - timedelta(days=1)
    )
    same_time_first = create_job(session, source, "2")
    same_time_second = create_job(session, source, "3")
    session.commit()

    response = client.get("/api/jobs")

    assert [item["id"] for item in response.json()] == [
        same_time_second.id,
        same_time_first.id,
        older.id,
    ]


def test_empty_results_and_invalid_publication_filters(client: TestClient) -> None:
    empty_response = client.get("/api/jobs")
    invalid_range = client.get(
        "/api/jobs",
        params={
            "published_from": (PUBLISHED_AT + timedelta(days=1)).isoformat(),
            "published_to": PUBLISHED_AT.isoformat(),
        },
    )
    naive_datetime = client.get(
        "/api/jobs",
        params={"published_from": "2026-08-10T12:00:00"},
    )

    assert empty_response.json() == []
    assert invalid_range.status_code == 422
    assert naive_datetime.status_code == 422


def test_response_exposes_public_source_and_skills_without_raw_payloads(
    client: TestClient,
    session: Session,
) -> None:
    source = create_source(session, "muse")
    python = create_skill(session, "python")
    job = create_job(session, source, "1")
    create_match(session, job, python)
    session.commit()

    response = client.get("/api/jobs")
    item = response.json()[0]

    assert item["source"] == {"code": "muse", "name": "Muse"}
    assert item["skills"] == [{"code": "python", "display_name": "Python"}]
    assert "raw_source_records" not in item
    assert "payload" not in item
