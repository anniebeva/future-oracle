from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.data_source import DataSource
from app.models.ingestion_run import IngestionRun
from app.models.job_posting import JobPosting
from app.models.job_skill_match import JobSkillMatch
from app.models.skill import Skill
from app.models.weekly_indicator import WeeklyIndicator
from app.services.job_eligibility import is_technical_posting

MINIMUM_ELIGIBLE_POSTINGS = 30
MINIMUM_COVERAGE_DAYS = 5


class WeeklyIndicatorService:
    """Calculate persisted source-level skill indicators for completed weeks"""

    def calculate_weekly_indicators(
        self,
        session: Session,
        period_start: datetime,
        period_end: datetime,
        *,
        now: datetime | None = None,
    ) -> list[WeeklyIndicator]:
        """Calculate indicators for every active source and skill"""
        calculation_time = _as_utc(now or datetime.now(UTC))
        _validate_completed_calendar_week(period_start, period_end, calculation_time)

        sources = session.scalars(
            select(DataSource)
            .where(DataSource.is_active.is_(True))
            .order_by(DataSource.id)
        ).all()
        skills = session.scalars(
            select(Skill).where(Skill.is_active.is_(True)).order_by(Skill.id)
        ).all()
        indicators: list[WeeklyIndicator] = []
        for source in sources:
            eligible_posting_ids = self._eligible_posting_ids(
                session, source, period_start, period_end
            )
            coverage_days = self._coverage_days(
                session, source.id, period_start, period_end
            )
            for skill in skills:
                indicators.append(
                    self._calculate_source_skill_week(
                        session=session,
                        source_id=source.id,
                        skill=skill,
                        period_start=period_start,
                        period_end=period_end,
                        eligible_posting_ids=eligible_posting_ids,
                        coverage_days=coverage_days,
                        calculated_at=calculation_time,
                    )
                )
        session.flush()
        return indicators

    def is_valid_source_week(self, indicator: WeeklyIndicator) -> bool:
        """Determine whether stored coverage and volume meet MVP thresholds"""
        return (
            indicator.eligible_postings_count >= MINIMUM_ELIGIBLE_POSTINGS
            and indicator.coverage_days >= MINIMUM_COVERAGE_DAYS
        )

    def _eligible_posting_ids(
        self,
        session: Session,
        source: DataSource,
        period_start: datetime,
        period_end: datetime,
    ) -> list[int]:
        """Return posting IDs eligible for one source and publication week"""
        postings = session.scalars(
            select(JobPosting).where(
                JobPosting.source_id == source.id,
                JobPosting.published_at >= period_start,
                JobPosting.published_at <= period_end,
            )
        ).all()
        return [
            posting.id
            for posting in postings
            if is_technical_posting(source.code, posting.category, posting.title)
        ]

    def _coverage_days(
        self,
        session: Session,
        source_id: int,
        period_start: datetime,
        period_end: datetime,
    ) -> int:
        """Count UTC dates with a successful completed ingestion run"""
        finished_at_values = session.scalars(
            select(IngestionRun.finished_at).where(
                IngestionRun.source_id == source_id,
                IngestionRun.status == "success",
                IngestionRun.finished_at.is_not(None),
                IngestionRun.finished_at >= period_start,
                IngestionRun.finished_at <= period_end,
            )
        ).all()
        return len(
            {_stored_utc_date(finished_at) for finished_at in finished_at_values}
        )

    def _calculate_source_skill_week(
        self,
        *,
        session: Session,
        source_id: int,
        skill: Skill,
        period_start: datetime,
        period_end: datetime,
        eligible_posting_ids: list[int],
        coverage_days: int,
        calculated_at: datetime,
    ) -> WeeklyIndicator:
        """Create or update one source-skill-week indicator"""
        matching_postings_count = self._matching_postings_count(
            session,
            skill.id,
            skill.dictionary_version,
            eligible_posting_ids,
        )
        eligible_postings_count = len(eligible_posting_ids)
        skill_share = (
            Decimal(matching_postings_count) / Decimal(eligible_postings_count)
            if eligible_postings_count
            else Decimal("0")
        )
        indicator = session.scalar(
            select(WeeklyIndicator).where(
                WeeklyIndicator.source_id == source_id,
                WeeklyIndicator.skill_id == skill.id,
                WeeklyIndicator.period_start == period_start,
                WeeklyIndicator.period_end == period_end,
            )
        )
        if indicator is None:
            indicator = WeeklyIndicator(
                source_id=source_id,
                skill_id=skill.id,
                period_start=period_start,
                period_end=period_end,
                eligible_postings_count=eligible_postings_count,
                matching_postings_count=matching_postings_count,
                skill_share=skill_share,
                coverage_days=coverage_days,
                calculated_at=calculated_at,
            )
            session.add(indicator)
        else:
            indicator.eligible_postings_count = eligible_postings_count
            indicator.matching_postings_count = matching_postings_count
            indicator.skill_share = skill_share
            indicator.coverage_days = coverage_days
            indicator.calculated_at = calculated_at
        return indicator

    def _matching_postings_count(
        self,
        session: Session,
        skill_id: int,
        dictionary_version: int,
        eligible_posting_ids: list[int],
    ) -> int:
        """Count distinct eligible postings with a current skill match"""
        if not eligible_posting_ids:
            return 0
        matching_posting_ids = session.scalars(
            select(JobSkillMatch.job_posting_id)
            .where(
                JobSkillMatch.skill_id == skill_id,
                JobSkillMatch.dictionary_version == dictionary_version,
                JobSkillMatch.job_posting_id.in_(eligible_posting_ids),
            )
            .distinct()
        ).all()
        return len(matching_posting_ids)


def is_valid_source_week(eligible_postings_count: int, coverage_days: int) -> bool:
    """Determine source-week validity from stored values"""
    return (
        eligible_postings_count >= MINIMUM_ELIGIBLE_POSTINGS
        and coverage_days >= MINIMUM_COVERAGE_DAYS
    )


def _validate_completed_calendar_week(
    period_start: datetime,
    period_end: datetime,
    now: datetime,
) -> None:
    """Require one completed UTC Monday-to-Sunday calendar week"""
    start = _as_utc(period_start)
    end = _as_utc(period_end)
    expected_end = datetime.combine(start.date(), time.min, UTC) + timedelta(
        days=7, microseconds=-1
    )
    current_week_start = datetime.combine(
        now.date() - timedelta(days=now.weekday()), time.min, UTC
    )
    if start != datetime.combine(start.date(), time.min, UTC) or end != expected_end:
        raise ValueError("Period must be a UTC Monday-to-Sunday calendar week")
    if start.weekday() != 0:
        raise ValueError("Period must start on Monday")
    if start >= current_week_start:
        raise ValueError("Current incomplete week cannot be calculated")


def _as_utc(value: datetime) -> datetime:
    """Validate and normalize a timezone-aware UTC datetime"""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Datetime must be timezone-aware UTC")
    if value.utcoffset() != timedelta(0):
        raise ValueError("Datetime must use UTC")
    return value.astimezone(UTC)


def _stored_utc_date(value: datetime) -> date:
    """Return a stored UTC date, supporting SQLite test values"""
    return value.date() if value.tzinfo is None else _as_utc(value).date()
