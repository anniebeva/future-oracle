"""
Demo seed script to populate the database with synthetic data for local testing.
Creates enough historical data to produce at least 3 valid completed weeks for forecasting.
"""

import random
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.models.data_source import DataSource
from app.models.ingestion_run import IngestionRun
from app.models.job_posting import JobPosting
from app.models.job_skill_match import JobSkillMatch
from app.models.skill import Skill
from app.services.skill_matching_service import SkillMatchingService
from app.services.weekly_indicator_service import WeeklyIndicatorService


DEMO_PREFIX = "demo_"
WEEKS_COUNT = 5
POSTINGS_PER_WEEK = 35
INGESTION_DAYS_PER_WEEK = 5


def _get_demo_source(session: Session) -> DataSource:
    """Get an existing data source for demo data"""
    source = session.scalar(
        select(DataSource)
        .where(DataSource.code.in_(["muse", "remotive"]))
        .order_by(DataSource.code)
    )

    if source is None:
        raise ValueError("No muse or remotive data source found")

    return source


def _create_skill_trends() -> dict[str, dict[str, float]]:
    """Create skill probabilities for each demo week"""
    return {
        "week1": {
            "python": 0.5,
            "django": 0.7,
            "fastapi": 0.3,
            "postgresql": 0.8,
            "docker": 0.6,
            "aws": 0.7,
        },
        "week2": {
            "python": 0.6,
            "django": 0.7,
            "fastapi": 0.4,
            "postgresql": 0.7,
            "docker": 0.6,
            "aws": 0.6,
        },
        "week3": {
            "python": 0.7,
            "django": 0.7,
            "fastapi": 0.6,
            "postgresql": 0.6,
            "docker": 0.65,
            "aws": 0.5,
        },
        "week4": {
            "python": 0.8,
            "django": 0.7,
            "fastapi": 0.7,
            "postgresql": 0.5,
            "docker": 0.65,
            "aws": 0.4,
        },
        "week5": {
            "python": 0.9,
            "django": 0.7,
            "fastapi": 0.8,
            "postgresql": 0.4,
            "docker": 0.7,
            "aws": 0.3,
        },
    }


def _create_demo_posting(
    session: Session,
    source: DataSource,
    week_start: datetime,
    posting_index: int,
    skill_trends: dict[str, float],
) -> JobPosting:
    """Create a single demo job posting"""
    base_titles = [
        "Python Developer",
        "Backend Engineer",
        "Software Engineer",
        "Full Stack Developer",
        "Data Engineer",
        "DevOps Engineer",
    ]

    included_skills = [
        skill_code
        for skill_code, probability in skill_trends.items()
        if random.random() < probability
    ]

    if not included_skills:
        included_skills = ["python"]

    title_skills = " ".join(included_skills[:2])
    title = f"{title_skills} {random.choice(base_titles)}"

    description = (
        f"Looking for a {title_skills} developer with experience in "
        f"{', '.join(included_skills)}. "
        "Requirements: 3+ years of experience in software development. "
        "Remote position."
    )

    external_id = (
        f"{DEMO_PREFIX}"
        f"{week_start.date().isoformat()}_"
        f"{posting_index}"
    )

    existing = session.scalar(
        select(JobPosting).where(
            JobPosting.source_id == source.id,
            JobPosting.external_id == external_id,
        )
    )

    if existing is not None:
        return existing

    published_at = week_start + timedelta(
        days=posting_index % 5,
        hours=8 + posting_index % 9,
    )

    posting = JobPosting(
        source_id=source.id,
        external_id=external_id,
        source_url=f"https://demo.example.com/jobs/{external_id}",
        title=title,
        company_name=f"Demo Company {posting_index + 1}",
        published_at=published_at,
        location_raw="Remote",
        location_scope="Remote",
        is_remote=True,
        category="software engineering",
        employment_type="Full-time",
        description_html=f"<p>{description}</p>",
        description_text=description,
        content_hash=f"{DEMO_PREFIX}hash_{external_id}",
        is_active=True,
    )

    session.add(posting)
    session.flush()

    return posting


def _create_demo_ingestion_runs(
    session: Session,
    source: DataSource,
    week_start: datetime,
) -> list[IngestionRun]:
    """Create successful ingestion runs on five different days"""
    runs: list[IngestionRun] = []

    for day_index in range(INGESTION_DAYS_PER_WEEK):
        run_date = week_start + timedelta(
            days=day_index,
            hours=10,
        )

        marker = (
            f"{DEMO_PREFIX}"
            f"ingestion_{week_start.date().isoformat()}_{day_index}"
        )

        existing = session.scalar(
            select(IngestionRun).where(
                IngestionRun.source_id == source.id,
                IngestionRun.error_message == marker,
            )
        )

        if existing is not None:
            runs.append(existing)
            continue

        run = IngestionRun(
            source_id=source.id,
            status="success",
            started_at=run_date,
            finished_at=run_date + timedelta(minutes=10),
            records_received=POSTINGS_PER_WEEK,
            error_message=marker,
        )

        session.add(run)
        runs.append(run)

    session.flush()

    return runs


def _delete_existing_demo_data(session: Session) -> None:
    """Remove existing demo postings and ingestion runs"""
    # First delete job skill matches for demo job postings to avoid FK constraint violations
    demo_posting_ids = session.scalars(
        select(JobPosting.id).where(
            JobPosting.external_id.like(f"{DEMO_PREFIX}%")
        )
    ).all()
    
    if demo_posting_ids:
        session.execute(
            delete(JobSkillMatch).where(
                JobSkillMatch.job_posting_id.in_(demo_posting_ids)
            )
        )

    # Then delete the demo job postings
    demo_postings = session.scalars(
        select(JobPosting).where(
            JobPosting.external_id.like(f"{DEMO_PREFIX}%")
        )
    ).all()

    for posting in demo_postings:
        session.delete(posting)

    demo_runs = session.scalars(
        select(IngestionRun).where(
            IngestionRun.error_message.like(f"{DEMO_PREFIX}%")
        )
    ).all()

    for run in demo_runs:
        session.delete(run)

    session.flush()


def seed_demo_data() -> None:
    """Create demo data for five completed weeks"""
    random.seed(42)

    db_generator = get_db_session()
    session = next(db_generator)

    try:
        source = _get_demo_source(session)

        active_skills = session.scalars(
            select(Skill).where(Skill.is_active.is_(True))
        ).all()

        if not active_skills:
            raise ValueError("No active skills found")

        _delete_existing_demo_data(session)

        skill_trends = _create_skill_trends()
        skill_matching_service = SkillMatchingService()
        weekly_indicator_service = WeeklyIndicatorService()

        today = datetime.now(UTC).date()
        monday = today - timedelta(days=today.weekday())

        first_week = monday - timedelta(weeks=WEEKS_COUNT)

        total_postings = 0
        total_matches = 0

        for week_index in range(WEEKS_COUNT):
            week_start_date = first_week + timedelta(weeks=week_index)

            week_start = datetime.combine(
                week_start_date,
                datetime.min.time(),
                tzinfo=UTC,
            )
            week_end = week_start + timedelta(
                days=7, microseconds=-1
            )

            week_key = f"week{week_index + 1}"

            print(
                f"Seeding {week_start_date} - "
                f"{(week_end - timedelta(seconds=1)).date()}"
            )

            _create_demo_ingestion_runs(
                session,
                source,
                week_start,
            )

            postings = [
                _create_demo_posting(
                    session=session,
                    source=source,
                    week_start=week_start,
                    posting_index=index,
                    skill_trends=skill_trends[week_key],
                )
                for index in range(POSTINGS_PER_WEEK)
            ]

            session.flush()

            posting_ids = [posting.id for posting in postings]

            matches = skill_matching_service.match_job_postings(
                session,
                posting_ids,
            )

            total_postings += len(postings)
            total_matches += len(matches)

            indicators = weekly_indicator_service.calculate_weekly_indicators(
                session,
                week_start,
                week_end,
            )

            print(
                f"  postings={len(postings)}, "
                f"skill_matches={len(matches)}, "
                f"indicators={len(indicators)}"
            )

            session.commit()

        print("\nDemo seeding complete")
        print(f"Total postings: {total_postings}")
        print(f"Total skill matches: {total_matches}")

    except Exception:
        session.rollback()
        raise

    finally:
        try:
            next(db_generator)
        except StopIteration:
            pass


if __name__ == "__main__":
    seed_demo_data()