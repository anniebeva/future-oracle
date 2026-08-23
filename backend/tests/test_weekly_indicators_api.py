from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from decimal import Decimal
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
from app.models.skill import Skill
from app.models.weekly_indicator import WeeklyIndicator

PERIOD_START = datetime(2026, 8, 10, tzinfo=UTC)
PERIOD_END = datetime(2026, 8, 16, 23, 59, 59, 999999, tzinfo=UTC)


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


def create_skill(session: Session, code: str, *, is_active: bool = True) -> Skill:
    skill = Skill(
        code=code,
        display_name=code.title(),
        dictionary_version=1,
        is_active=is_active,
    )
    session.add(skill)
    session.flush()
    return skill


def create_indicator(
    session: Session,
    source: DataSource,
    skill: Skill,
    *,
    period_start: datetime = PERIOD_START,
    period_end: datetime = PERIOD_END,
    share: Decimal = Decimal("0.5"),
) -> WeeklyIndicator:
    indicator = WeeklyIndicator(
        source_id=source.id,
        skill_id=skill.id,
        period_start=period_start,
        period_end=period_end,
        eligible_postings_count=10,
        matching_postings_count=5,
        skill_share=share,
        coverage_days=5,
        calculated_at=period_end + timedelta(hours=1),
    )
    session.add(indicator)
    session.commit()
    return indicator


def test_endpoint_returns_persisted_indicator_with_source_and_skill(
    client: TestClient, session: Session
) -> None:
    source = create_source(session, "muse")
    skill = create_skill(session, "python")
    create_indicator(session, source, skill)

    response = client.get("/api/indicators/weekly")

    assert response.status_code == 200
    assert response.json() == [
        {
            "source": {"code": "muse", "name": "Muse"},
            "skill": {"code": "python", "display_name": "Python"},
            "period_start": "2026-08-10T00:00:00Z",
            "period_end": "2026-08-16T23:59:59.999999Z",
            "eligible_postings_count": 10,
            "matching_postings_count": 5,
            "skill_share": "0.50000000",
            "coverage_days": 5,
            "calculated_at": "2026-08-17T00:59:59.999999Z",
        }
    ]


def test_source_and_skill_filters_work(client: TestClient, session: Session) -> None:
    muse = create_source(session, "muse")
    remotive = create_source(session, "remotive")
    python = create_skill(session, "python")
    docker = create_skill(session, "docker")
    create_indicator(session, muse, python)
    create_indicator(session, remotive, docker)

    source_response = client.get("/api/indicators/weekly", params={"source": "muse"})
    skill_response = client.get("/api/indicators/weekly", params={"skill": "docker"})

    assert [item["source"]["code"] for item in source_response.json()] == ["muse"]
    assert [item["skill"]["code"] for item in skill_response.json()] == ["docker"]


def test_period_filters_and_combined_filters_work(
    client: TestClient, session: Session
) -> None:
    muse = create_source(session, "muse")
    remotive = create_source(session, "remotive")
    python = create_skill(session, "python")
    older_start = PERIOD_START - timedelta(days=7)
    older_end = PERIOD_END - timedelta(days=7)
    create_indicator(
        session, muse, python, period_start=older_start, period_end=older_end
    )
    create_indicator(session, muse, python)
    create_indicator(session, remotive, python)

    start_response = client.get(
        "/api/indicators/weekly",
        params={"period_start": PERIOD_START.isoformat()},
    )
    end_response = client.get(
        "/api/indicators/weekly",
        params={"period_end": older_end.isoformat()},
    )
    combined_response = client.get(
        "/api/indicators/weekly",
        params={
            "source": "muse",
            "skill": "python",
            "period_start": PERIOD_START.isoformat(),
            "period_end": PERIOD_END.isoformat(),
        },
    )

    assert len(start_response.json()) == 2
    assert len(end_response.json()) == 1
    assert len(combined_response.json()) == 1
    assert combined_response.json()[0]["source"]["code"] == "muse"


def test_inactive_sources_and_skills_are_excluded(
    client: TestClient, session: Session
) -> None:
    active_source = create_source(session, "muse")
    inactive_source = create_source(session, "remotive", is_active=False)
    active_skill = create_skill(session, "python")
    inactive_skill = create_skill(session, "docker", is_active=False)
    create_indicator(session, active_source, active_skill)
    create_indicator(session, inactive_source, active_skill)
    create_indicator(session, active_source, inactive_skill)

    response = client.get("/api/indicators/weekly")

    assert len(response.json()) == 1
    assert response.json()[0]["source"]["code"] == "muse"
    assert response.json()[0]["skill"]["code"] == "python"


def test_results_are_newest_first_with_deterministic_source_and_skill_order(
    client: TestClient,
    session: Session,
) -> None:
    muse = create_source(session, "muse")
    remotive = create_source(session, "remotive")
    docker = create_skill(session, "docker")
    python = create_skill(session, "python")
    newer_start = PERIOD_START + timedelta(days=7)
    newer_end = PERIOD_END + timedelta(days=7)
    create_indicator(
        session, remotive, python, period_start=newer_start, period_end=newer_end
    )
    create_indicator(
        session, muse, docker, period_start=newer_start, period_end=newer_end
    )
    create_indicator(
        session, muse, python, period_start=PERIOD_START, period_end=PERIOD_END
    )

    response = client.get("/api/indicators/weekly")

    assert [
        (item["period_start"], item["source"]["code"], item["skill"]["code"])
        for item in response.json()
    ] == [
        ("2026-08-17T00:00:00Z", "muse", "docker"),
        ("2026-08-17T00:00:00Z", "remotive", "python"),
        ("2026-08-10T00:00:00Z", "muse", "python"),
    ]


def test_empty_result_is_an_empty_list(client: TestClient) -> None:
    response = client.get("/api/indicators/weekly")

    assert response.status_code == 200
    assert response.json() == []


def test_invalid_period_range_and_naive_datetimes_return_422(
    client: TestClient,
) -> None:
    invalid_range = client.get(
        "/api/indicators/weekly",
        params={
            "period_start": PERIOD_END.isoformat(),
            "period_end": PERIOD_START.isoformat(),
        },
    )
    naive_datetime = client.get(
        "/api/indicators/weekly",
        params={"period_start": "2026-08-10T00:00:00"},
    )

    assert invalid_range.status_code == 422
    assert naive_datetime.status_code == 422


def test_response_matches_weekly_indicator_schema(
    client: TestClient, session: Session
) -> None:
    source = create_source(session, "muse")
    skill = create_skill(session, "python")
    create_indicator(session, source, skill)

    response = client.get("/api/indicators/weekly")

    assert set(response.json()[0]) == {
        "source",
        "skill",
        "period_start",
        "period_end",
        "eligible_postings_count",
        "matching_postings_count",
        "skill_share",
        "coverage_days",
        "calculated_at",
    }
