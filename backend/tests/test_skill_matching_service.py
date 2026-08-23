from collections.abc import Iterator
from datetime import datetime
from typing import Any

import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base, load_models
from app.models.data_source import DataSource
from app.models.job_posting import JobPosting
from app.models.job_skill_match import JobSkillMatch
from app.models.skill import Skill
from app.services.skill_matching_service import SkillMatchingService
from app.services.skill_seed import (INITIAL_DICTIONARY_VERSION,
                                     seed_initial_skills)


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
    seed_initial_skills(database_session)
    database_session.commit()
    yield database_session
    database_session.close()
    Base.metadata.drop_all(engine)
    engine.dispose()


def create_posting(
    session: Session,
    *,
    title: str | None = "Developer",
    description: str | None = "",
) -> JobPosting:
    source = DataSource(code="test", name="Test", base_url="https://test.example")
    session.add(source)
    session.flush()
    posting = JobPosting(
        source_id=source.id,
        external_id="job-1",
        source_url="https://test.example/job-1",
        title=title or "",
        published_at=datetime.fromisoformat("2026-08-21T10:00:00+00:00"),
        description_text=description,
        content_hash="0" * 64,
        is_active=True,
    )
    session.add(posting)
    session.commit()
    return posting


def matches_for(session: Session, posting: JobPosting) -> list[JobSkillMatch]:
    return session.scalars(
        select(JobSkillMatch)
        .where(JobSkillMatch.job_posting_id == posting.id)
        .order_by(JobSkillMatch.skill_id)
    ).all()


def skill_match(session: Session, posting: JobPosting, code: str) -> JobSkillMatch:
    return session.scalars(
        select(JobSkillMatch)
        .join(Skill)
        .where(JobSkillMatch.job_posting_id == posting.id, Skill.code == code)
    ).one()


def test_python_match_in_title(session: Session) -> None:
    posting = create_posting(session, title="Senior PYTHON Developer")

    SkillMatchingService().match_job_posting(session, posting.id)

    match = skill_match(session, posting, "python")
    assert match.matched_in_title is True
    assert match.matched_in_description is False
    assert match.match_count == 1


def test_python_match_in_description_and_multiple_aliases(session: Session) -> None:
    posting = create_posting(
        session,
        title="Senior Python Developer",
        description="Python and Python 3 experience required",
    )

    SkillMatchingService().match_job_posting(session, posting.id)

    match = skill_match(session, posting, "python")
    assert len(matches_for(session, posting)) == 1
    assert match.matched_alias == "python"
    assert match.matched_in_title is True
    assert match.matched_in_description is True
    assert match.match_count == 3


def test_fastapi_and_postgresql_aliases(session: Session) -> None:
    posting = create_posting(
        session,
        title="Fast API Engineer",
        description="PostgreSQL and Postgres",
    )

    SkillMatchingService().match_job_posting(session, posting.id)

    assert skill_match(session, posting, "fastapi").match_count == 1
    assert skill_match(session, posting, "postgresql").match_count == 2


def test_word_boundaries_prevent_false_positives(session: Session) -> None:
    posting = create_posting(
        session,
        title="AWSome developer",
        description="postgreSQLish dockerized containerizations",
    )

    SkillMatchingService().match_job_posting(session, posting.id)

    assert matches_for(session, posting) == []


def test_django_docker_containerization_and_standalone_aws_match(
    session: Session,
) -> None:
    posting = create_posting(
        session,
        title="Django and Docker Engineer",
        description="AWS and containerization experience required",
    )

    SkillMatchingService().match_job_posting(session, posting.id)

    assert skill_match(session, posting, "django").match_count == 1
    assert skill_match(session, posting, "docker").match_count == 2
    assert skill_match(session, posting, "aws").matched_alias == "aws"


def test_no_matching_skills_creates_no_records(session: Session) -> None:
    posting = create_posting(
        session, title="Java Engineer", description="Kubernetes experience"
    )

    result = SkillMatchingService().match_job_posting(session, posting.id)

    assert result == []
    assert matches_for(session, posting) == []


def test_matching_twice_does_not_create_duplicates(session: Session) -> None:
    posting = create_posting(session, title="Django Developer")
    service = SkillMatchingService()

    service.match_job_posting(session, posting.id)
    service.match_job_posting(session, posting.id)

    assert len(matches_for(session, posting)) == 1


def test_rerun_removes_stale_current_version_match(session: Session) -> None:
    posting = create_posting(session, title="Docker Developer")
    service = SkillMatchingService()
    service.match_job_posting(session, posting.id)
    posting.title = "Java Developer"
    session.commit()

    service.match_job_posting(session, posting.id)

    assert matches_for(session, posting) == []


def test_rerun_preserves_older_dictionary_versions(session: Session) -> None:
    posting = create_posting(session, title="Docker Developer")
    docker = session.scalars(select(Skill).where(Skill.code == "docker")).one()
    session.add(
        JobSkillMatch(
            job_posting_id=posting.id,
            skill_id=docker.id,
            dictionary_version=0,
            matched_alias="docker",
            matched_in_title=True,
            matched_in_description=False,
            match_count=1,
        )
    )
    session.commit()
    posting.title = "Java Developer"
    session.commit()

    SkillMatchingService().match_job_posting(session, posting.id)

    assert (
        session.scalars(
            select(JobSkillMatch).where(
                JobSkillMatch.job_posting_id == posting.id,
                JobSkillMatch.dictionary_version == 0,
            )
        )
        .one()
        .matched_alias
        == "docker"
    )
    assert matches_for(session, posting)[0].dictionary_version == 0


def test_missing_title_and_description_do_not_crash(session: Session) -> None:
    posting = create_posting(session, title=None, description=None)

    result = SkillMatchingService().match_job_posting(session, posting.id)

    assert result == []


def test_initial_seed_uses_version_one(session: Session) -> None:
    skills = session.scalars(select(Skill).order_by(Skill.code)).all()

    assert len(skills) == 6
    assert {skill.dictionary_version for skill in skills} == {
        INITIAL_DICTIONARY_VERSION
    }
