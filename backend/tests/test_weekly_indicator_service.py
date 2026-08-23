from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from decimal import Decimal
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
from app.models.job_skill_match import JobSkillMatch
from app.models.skill import Skill
from app.models.weekly_indicator import WeeklyIndicator
from app.services.weekly_indicator_service import (WeeklyIndicatorService,
                                                   is_valid_source_week)

WEEK_START = datetime(2026, 8, 10, tzinfo=UTC)
WEEK_END = datetime(2026, 8, 16, 23, 59, 59, 999999, tzinfo=UTC)
CALCULATION_TIME = datetime(2026, 8, 24, 12, tzinfo=UTC)


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


def create_source(session: Session, code: str) -> DataSource:
    source = DataSource(
        code=code, name=code.title(), base_url=f"https://{code}.example"
    )
    session.add(source)
    session.flush()
    return source


def create_skill(session: Session, code: str = "python", version: int = 1) -> Skill:
    skill = Skill(code=code, display_name=code.title(), dictionary_version=version)
    session.add(skill)
    session.flush()
    return skill


def create_posting(
    session: Session,
    source: DataSource,
    external_id: str,
    *,
    published_at: datetime = WEEK_START,
    title: str = "Software Engineer",
    category: str | None = None,
) -> JobPosting:
    posting = JobPosting(
        source_id=source.id,
        external_id=external_id,
        source_url=f"https://{source.code}.example/{external_id}",
        title=title,
        published_at=published_at,
        category=category,
        content_hash=external_id.zfill(64),
        is_active=True,
    )
    session.add(posting)
    session.flush()
    return posting


def create_match(
    session: Session,
    posting: JobPosting,
    skill: Skill,
    *,
    dictionary_version: int = 1,
) -> None:
    session.add(
        JobSkillMatch(
            job_posting_id=posting.id,
            skill_id=skill.id,
            dictionary_version=dictionary_version,
            matched_alias=skill.code,
            matched_in_title=True,
            matched_in_description=False,
            match_count=1,
        )
    )
    session.flush()


def create_run(
    session: Session,
    source: DataSource,
    finished_at: datetime,
    *,
    status: str = "success",
    started_at: datetime | None = None,
) -> None:
    session.add(
        IngestionRun(
            source_id=source.id,
            status=status,
            started_at=started_at or finished_at,
            finished_at=finished_at,
            records_received=1,
        )
    )
    session.flush()


def calculate(session: Session) -> list[WeeklyIndicator]:
    return WeeklyIndicatorService().calculate_weekly_indicators(
        session,
        WEEK_START,
        WEEK_END,
        now=CALCULATION_TIME,
    )


def test_monday_sunday_boundaries_and_publication_date_determine_week(
    session: Session,
) -> None:
    source = create_source(session, "muse")
    skill = create_skill(session)
    monday = create_posting(session, source, "1", published_at=WEEK_START)
    sunday = create_posting(session, source, "2", published_at=WEEK_END)
    create_posting(
        session, source, "3", published_at=WEEK_START - timedelta(microseconds=1)
    )
    create_posting(
        session, source, "4", published_at=WEEK_END + timedelta(microseconds=1)
    )
    create_match(session, monday, skill)
    create_match(session, sunday, skill)

    indicator = calculate(session)[0]

    assert indicator.eligible_postings_count == 2
    assert indicator.matching_postings_count == 2
    assert indicator.skill_share == Decimal("1")


def test_current_incomplete_week_is_rejected(session: Session) -> None:
    create_source(session, "muse")
    create_skill(session)
    current_week_start = datetime(2026, 8, 17, tzinfo=UTC)
    current_week_end = datetime(2026, 8, 23, 23, 59, 59, 999999, tzinfo=UTC)

    with pytest.raises(ValueError, match="Current incomplete week"):
        WeeklyIndicatorService().calculate_weekly_indicators(
            session,
            current_week_start,
            current_week_end,
            now=datetime(2026, 8, 20, 12, tzinfo=UTC),
        )


def test_technical_category_and_title_are_eligible_but_non_technical_titles_are_excluded(
    session: Session,
) -> None:
    source = create_source(session, "muse")
    create_skill(session)
    create_posting(session, source, "1", title="Python Developer")
    create_posting(
        session, source, "2", title="Generalist", category="Software Engineering"
    )
    create_posting(
        session, source, "3", title="Recruiter", category="Software Engineering"
    )
    create_posting(session, source, "4", title="Sales Manager")
    create_posting(session, source, "5", title="Product Marketing Manager")
    create_posting(session, source, "6", title="Accountant")
    create_posting(session, source, "7", title="Customer Support Specialist")

    indicator = calculate(session)[0]

    assert indicator.eligible_postings_count == 2


def test_current_version_matches_are_counted_once_per_posting(session: Session) -> None:
    source = create_source(session, "muse")
    skill = create_skill(session)
    matched = create_posting(session, source, "1")
    unmatched = create_posting(session, source, "2")
    create_match(session, matched, skill)
    create_match(session, matched, skill, dictionary_version=0)

    indicator = calculate(session)[0]

    assert indicator.eligible_postings_count == 2
    assert indicator.matching_postings_count == 1
    assert indicator.skill_share == Decimal("0.5")
    assert unmatched.id != matched.id


def test_indicators_are_separate_for_sources_and_skills(session: Session) -> None:
    muse = create_source(session, "muse")
    remotive = create_source(session, "remotive")
    python = create_skill(session, "python")
    docker = create_skill(session, "docker")
    muse_posting = create_posting(session, muse, "1")
    remotive_posting = create_posting(session, remotive, "1")
    create_match(session, muse_posting, python)
    create_match(session, remotive_posting, docker)

    indicators = calculate(session)
    indicator_by_source_skill = {
        (indicator.source_id, indicator.skill_id): indicator for indicator in indicators
    }

    assert len(indicators) == 4
    assert indicator_by_source_skill[(muse.id, python.id)].matching_postings_count == 1
    assert indicator_by_source_skill[(muse.id, docker.id)].matching_postings_count == 0
    assert (
        indicator_by_source_skill[(remotive.id, python.id)].matching_postings_count == 0
    )
    assert (
        indicator_by_source_skill[(remotive.id, docker.id)].matching_postings_count == 1
    )


def test_coverage_counts_only_distinct_successful_finished_dates(
    session: Session,
) -> None:
    source = create_source(session, "muse")
    create_skill(session)
    for day_offset in range(5):
        create_run(session, source, WEEK_START + timedelta(days=day_offset, hours=12))
    create_run(session, source, WEEK_START + timedelta(hours=1))
    create_run(session, source, WEEK_START + timedelta(days=5), status="failed")

    indicator = calculate(session)[0]

    assert indicator.coverage_days == 5
    assert WeeklyIndicatorService().is_valid_source_week(indicator) is False


def test_successful_runs_outside_the_requested_week_do_not_count_for_coverage(
    session: Session,
) -> None:
    source = create_source(session, "muse")
    create_skill(session)
    create_run(session, source, WEEK_START - timedelta(microseconds=1))
    create_run(session, source, WEEK_START + timedelta(hours=12))
    create_run(session, source, WEEK_END + timedelta(microseconds=1))

    indicator = calculate(session)[0]

    assert indicator.coverage_days == 1


def test_cross_midnight_run_counts_for_its_monday_completion_day(
    session: Session,
) -> None:
    source = create_source(session, "muse")
    create_skill(session)
    create_run(
        session,
        source,
        WEEK_START + timedelta(minutes=1),
        started_at=WEEK_START - timedelta(minutes=1),
    )

    indicator = calculate(session)[0]

    assert indicator.coverage_days == 1


def test_low_eligible_count_is_persisted_and_marked_invalid_by_helper(
    session: Session,
) -> None:
    source = create_source(session, "muse")
    create_skill(session)
    create_posting(session, source, "1")
    for day_offset in range(5):
        create_run(session, source, WEEK_START + timedelta(days=day_offset, hours=12))

    indicator = calculate(session)[0]

    assert indicator.eligible_postings_count == 1
    assert (
        is_valid_source_week(indicator.eligible_postings_count, indicator.coverage_days)
        is False
    )
    assert session.scalar(select(WeeklyIndicator)) is indicator


def test_low_coverage_is_persisted_and_marked_invalid_by_helper(
    session: Session,
) -> None:
    source = create_source(session, "muse")
    create_skill(session)
    for number in range(30):
        create_posting(session, source, str(number))
    create_run(session, source, WEEK_START + timedelta(hours=12))

    indicator = calculate(session)[0]

    assert indicator.eligible_postings_count == 30
    assert indicator.coverage_days == 1
    assert (
        is_valid_source_week(indicator.eligible_postings_count, indicator.coverage_days)
        is False
    )


def test_recalculation_updates_existing_indicator_without_duplicates(
    session: Session,
) -> None:
    source = create_source(session, "muse")
    skill = create_skill(session)
    posting = create_posting(session, source, "1")

    first_indicator = calculate(session)[0]
    create_match(session, posting, skill)
    second_indicator = calculate(session)[0]

    assert first_indicator.id == second_indicator.id
    assert second_indicator.matching_postings_count == 1
    assert session.scalars(select(WeeklyIndicator)).all() == [second_indicator]


def test_zero_matching_postings_use_zero_decimal_share(session: Session) -> None:
    source = create_source(session, "muse")
    create_skill(session)
    create_posting(session, source, "1")

    indicator = calculate(session)[0]

    assert indicator.eligible_postings_count == 1
    assert indicator.matching_postings_count == 0
    assert indicator.skill_share == Decimal("0")


def test_zero_eligible_postings_use_zero_decimal_share(session: Session) -> None:
    source = create_source(session, "muse")
    skill = create_skill(session)
    create_posting(session, source, "1", title="Recruiter")

    indicator = calculate(session)[0]

    assert indicator.eligible_postings_count == 0
    assert indicator.matching_postings_count == 0
    assert indicator.skill_share == Decimal("0")
    assert skill.id == indicator.skill_id
