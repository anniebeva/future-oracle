from collections.abc import Iterator
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


def create_source(session: Session, code: str, *, is_active: bool = True) -> None:
    session.add(
        DataSource(
            code=code,
            name=code.title(),
            base_url=f"https://{code}.example",
            is_active=is_active,
        )
    )
    session.commit()


def create_skill(session: Session, code: str, *, is_active: bool = True) -> None:
    session.add(
        Skill(
            code=code,
            display_name=code.title(),
            dictionary_version=1,
            is_active=is_active,
        )
    )
    session.commit()


def test_sources_return_active_records_in_code_order_with_public_fields(
    client: TestClient,
    session: Session,
) -> None:
    create_source(session, "remotive")
    create_source(session, "muse")
    create_source(session, "inactive", is_active=False)

    response = client.get("/api/sources")

    assert response.status_code == 200
    assert response.json() == [
        {"code": "muse", "name": "Muse", "base_url": "https://muse.example"},
        {
            "code": "remotive",
            "name": "Remotive",
            "base_url": "https://remotive.example",
        },
    ]
    assert set(response.json()[0]) == {"code", "name", "base_url"}


def test_skills_return_active_records_in_code_order_with_public_fields(
    client: TestClient,
    session: Session,
) -> None:
    create_skill(session, "python")
    create_skill(session, "docker")
    create_skill(session, "inactive", is_active=False)

    response = client.get("/api/skills")

    assert response.status_code == 200
    assert response.json() == [
        {"code": "docker", "display_name": "Docker", "dictionary_version": 1},
        {"code": "python", "display_name": "Python", "dictionary_version": 1},
    ]
    assert set(response.json()[0]) == {"code", "display_name", "dictionary_version"}


def test_empty_reference_lists_are_empty(client: TestClient) -> None:
    assert client.get("/api/sources").json() == []
    assert client.get("/api/skills").json() == []
