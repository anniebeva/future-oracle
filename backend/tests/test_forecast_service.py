from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base, load_models
from app.models.data_source import DataSource
from app.models.skill import Skill
from app.models.weekly_indicator import WeeklyIndicator
from app.services.forecast_service import (
    ForecastResult,
    ForecastService,
    InsufficientDataResult,
)


@compiles(JSONB, "sqlite")
def compile_jsonb_for_sqlite(
    type_: JSONB,
    compiler: Any,
    **kwargs: Any,
) -> str:
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
    def enable_foreign_keys(
        dbapi_connection: Any,
        connection_record: Any,
    ) -> None:
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
        code=code,
        name=code.title(),
        base_url=f"https://{code}.example",
    )
    session.add(source)
    session.flush()
    return source


def create_skill(session: Session, code: str = "python") -> Skill:
    skill = Skill(
        code=code,
        display_name=code.title(),
    )
    session.add(skill)
    session.flush()
    return skill


def create_weekly_indicator(
    session: Session,
    source: DataSource,
    skill: Skill,
    period_start: datetime,
    *,
    skill_share: float = 0.15,
    eligible_postings_count: int = 50,
    coverage_days: int = 7,
) -> WeeklyIndicator:
    indicator = WeeklyIndicator(
        source_id=source.id,
        skill_id=skill.id,
        period_start=period_start,
        period_end=period_start + timedelta(days=6, microseconds=-1),
        eligible_postings_count=eligible_postings_count,
        matching_postings_count=int(
            eligible_postings_count * skill_share,
        ),
        skill_share=Decimal(str(skill_share)),
        coverage_days=coverage_days,
        calculated_at=period_start + timedelta(days=8),
    )

    session.add(indicator)
    session.flush()

    return indicator


def test_strong_positive_trend_produces_growing_forecast(
    session: Session,
) -> None:
    """Test that a strong positive trend produces a growing forecast"""
    source = create_source(session, "muse")
    skill = create_skill(session, "python")

    base_date = datetime(2026, 8, 10, tzinfo=UTC)

    create_weekly_indicator(
        session,
        source,
        skill,
        base_date - timedelta(weeks=3),
        skill_share=0.12,
    )
    create_weekly_indicator(
        session,
        source,
        skill,
        base_date - timedelta(weeks=2),
        skill_share=0.15,
    )
    create_weekly_indicator(
        session,
        source,
        skill,
        base_date - timedelta(weeks=1),
        skill_share=0.18,
    )
    create_weekly_indicator(
        session,
        source,
        skill,
        base_date,
        skill_share=0.22,
        coverage_days=6,
    )

    service = ForecastService(session)
    result = service.forecast_skill_demand("python")

    assert isinstance(result, ForecastResult)
    assert result.direction == "growing"
    assert result.score > 0.2
    assert result.confidence > 50
    assert "Trend: +4.0pp" in result.explanation


def test_strong_negative_trend_produces_declining_forecast(
    session: Session,
) -> None:
    """Test that a strong negative trend produces a declining forecast"""
    source = create_source(session, "muse")
    skill = create_skill(session, "cobol")

    base_date = datetime(2026, 8, 10, tzinfo=UTC)

    create_weekly_indicator(
        session,
        source,
        skill,
        base_date - timedelta(weeks=3),
        skill_share=0.25,
    )
    create_weekly_indicator(
        session,
        source,
        skill,
        base_date - timedelta(weeks=2),
        skill_share=0.20,
    )
    create_weekly_indicator(
        session,
        source,
        skill,
        base_date - timedelta(weeks=1),
        skill_share=0.16,
    )
    create_weekly_indicator(
        session,
        source,
        skill,
        base_date,
        skill_share=0.12,
    )

    service = ForecastService(session)
    result = service.forecast_skill_demand("cobol")

    assert isinstance(result, ForecastResult)
    assert result.direction == "declining"
    assert result.score < -0.2
    assert "Trend: -4.0pp" in result.explanation


def test_small_changes_produce_stable_forecast(
    session: Session,
) -> None:
    """Test that small changes produce a stable forecast"""
    source = create_source(session, "muse")
    skill = create_skill(session, "javascript")

    base_date = datetime(2026, 8, 10, tzinfo=UTC)

    create_weekly_indicator(
        session,
        source,
        skill,
        base_date - timedelta(weeks=3),
        skill_share=0.15,
    )
    create_weekly_indicator(
        session,
        source,
        skill,
        base_date - timedelta(weeks=2),
        skill_share=0.155,
    )
    create_weekly_indicator(
        session,
        source,
        skill,
        base_date - timedelta(weeks=1),
        skill_share=0.152,
    )
    create_weekly_indicator(
        session,
        source,
        skill,
        base_date,
        skill_share=0.153,
    )

    service = ForecastService(session)
    result = service.forecast_skill_demand("javascript")

    assert isinstance(result, ForecastResult)
    assert result.direction == "stable"
    assert -0.2 <= result.score <= 0.2


def test_negative_acceleration(session: Session) -> None:
    """Test negative acceleration in trend produces lower scores"""
    source = create_source(session, "muse")
    skill = create_skill(session, "php")

    base_date = datetime(2026, 8, 10, tzinfo=UTC)

    # Create 4 weeks with an accelerating negative trend:
    # 25% -> 20% -> 14% -> 6%
    # Changes: -5pp -> -6pp -> -8pp
    create_weekly_indicator(
        session,
        source,
        skill,
        base_date - timedelta(weeks=3),
        skill_share=0.25,
    )
    create_weekly_indicator(
        session,
        source,
        skill,
        base_date - timedelta(weeks=2),
        skill_share=0.20,
    )
    create_weekly_indicator(
        session,
        source,
        skill,
        base_date - timedelta(weeks=1),
        skill_share=0.14,
    )
    create_weekly_indicator(
        session,
        source,
        skill,
        base_date,
        skill_share=0.06,
    )

    service = ForecastService(session)
    result = service.forecast_skill_demand("php")

    assert isinstance(result, ForecastResult)
    assert result.direction == "declining"
    assert "Trend: -8.0pp" in result.explanation
    assert "Momentum: -2.0pp" in result.explanation


def test_score_clamping_at_extremes(session: Session) -> None:
    """Test that scores are properly clamped at extremes"""
    source = create_source(session, "muse")
    skill = create_skill(session, "blockchain")

    base_date = datetime(2026, 8, 10, tzinfo=UTC)

    create_weekly_indicator(
        session,
        source,
        skill,
        base_date - timedelta(weeks=3),
        skill_share=0.05,
    )
    create_weekly_indicator(
        session,
        source,
        skill,
        base_date - timedelta(weeks=2),
        skill_share=0.10,
    )
    create_weekly_indicator(
        session,
        source,
        skill,
        base_date - timedelta(weeks=1),
        skill_share=0.20,
    )
    create_weekly_indicator(
        session,
        source,
        skill,
        base_date,
        skill_share=0.40,
    )

    service = ForecastService(session)
    result = service.forecast_skill_demand("blockchain")

    assert isinstance(result, ForecastResult)
    assert -1.0 <= result.score <= 1.0


def test_confidence_calculation(session: Session) -> None:
    """Test confidence calculation based on coverage and volume"""
    source = create_source(session, "muse")
    skill = create_skill(session, "rust")

    base_date = datetime(2026, 8, 10, tzinfo=UTC)

    create_weekly_indicator(
        session,
        source,
        skill,
        base_date - timedelta(weeks=2),
        skill_share=0.10,
    )
    create_weekly_indicator(
        session,
        source,
        skill,
        base_date - timedelta(weeks=1),
        skill_share=0.12,
    )
    create_weekly_indicator(
        session,
        source,
        skill,
        base_date,
        skill_share=0.15,
        coverage_days=5,
        eligible_postings_count=75,
    )

    service = ForecastService(session)
    result = service.forecast_skill_demand("rust")

    assert isinstance(result, ForecastResult)

    # 100 * (0.6 * 5/7 + 0.4 * 75/100) ≈ 72.86
    assert 70 <= result.confidence <= 75


def test_exactly_three_weeks_of_data(session: Session) -> None:
    """Test that with exactly 3 weeks, risk cannot be low"""
    source = create_source(session, "muse")
    skill = create_skill(session, "typescript")

    base_date = datetime(2026, 8, 10, tzinfo=UTC)

    create_weekly_indicator(
        session,
        source,
        skill,
        base_date - timedelta(weeks=2),
        skill_share=0.10,
    )
    create_weekly_indicator(
        session,
        source,
        skill,
        base_date - timedelta(weeks=1),
        skill_share=0.15,
    )
    create_weekly_indicator(
        session,
        source,
        skill,
        base_date,
        skill_share=0.20,
        coverage_days=7,
        eligible_postings_count=100,
    )

    service = ForecastService(session)
    result = service.forecast_skill_demand("typescript")

    assert isinstance(result, ForecastResult)
    assert result.risk in ["medium", "high"]


def test_insufficient_historical_data(session: Session) -> None:
    """Test handling of insufficient historical data"""
    source = create_source(session, "muse")
    skill = create_skill(session, "fortran")

    base_date = datetime(2026, 8, 10, tzinfo=UTC)

    create_weekly_indicator(
        session,
        source,
        skill,
        base_date - timedelta(weeks=1),
        skill_share=0.10,
    )
    create_weekly_indicator(
        session,
        source,
        skill,
        base_date,
        skill_share=0.15,
    )

    service = ForecastService(session)
    result = service.forecast_skill_demand("fortran")

    assert isinstance(result, InsufficientDataResult)
    assert "Need at least 3 complete weeks" in result.reason


def test_week_failing_eligible_postings_threshold(
    session: Session,
) -> None:
    """Test that weeks failing eligible postings threshold are filtered out"""
    source = create_source(session, "muse")
    skill = create_skill(session, "perl")

    base_date = datetime(2026, 8, 10, tzinfo=UTC)

    create_weekly_indicator(
        session,
        source,
        skill,
        base_date - timedelta(weeks=3),
        skill_share=0.10,
        eligible_postings_count=25,
    )
    create_weekly_indicator(
        session,
        source,
        skill,
        base_date - timedelta(weeks=2),
        skill_share=0.12,
    )
    create_weekly_indicator(
        session,
        source,
        skill,
        base_date - timedelta(weeks=1),
        skill_share=0.15,
    )
    create_weekly_indicator(
        session,
        source,
        skill,
        base_date,
        skill_share=0.18,
    )

    service = ForecastService(session)
    result = service.forecast_skill_demand("perl")

    assert isinstance(result, ForecastResult)


def test_week_failing_coverage_days_threshold(
    session: Session,
) -> None:
    """Test that weeks failing coverage days threshold are filtered out"""
    source = create_source(session, "muse")
    skill = create_skill(session, "scala")

    base_date = datetime(2026, 8, 10, tzinfo=UTC)

    create_weekly_indicator(
        session,
        source,
        skill,
        base_date - timedelta(weeks=3),
        skill_share=0.10,
        coverage_days=3,
    )
    create_weekly_indicator(
        session,
        source,
        skill,
        base_date - timedelta(weeks=2),
        skill_share=0.12,
    )
    create_weekly_indicator(
        session,
        source,
        skill,
        base_date - timedelta(weeks=1),
        skill_share=0.15,
    )
    create_weekly_indicator(
        session,
        source,
        skill,
        base_date,
        skill_share=0.18,
    )

    service = ForecastService(session)
    result = service.forecast_skill_demand("scala")

    assert isinstance(result, ForecastResult)


def test_boundary_values_around_direction_thresholds(
    session: Session,
) -> None:
    """Test boundary values around direction thresholds"""
    source = create_source(session, "muse")
    skill = create_skill(session, "elixir")

    base_date = datetime(2026, 8, 10, tzinfo=UTC)

    create_weekly_indicator(
        session,
        source,
        skill,
        base_date - timedelta(weeks=3),
        skill_share=0.10,
    )
    create_weekly_indicator(
        session,
        source,
        skill,
        base_date - timedelta(weeks=2),
        skill_share=0.11,
    )
    create_weekly_indicator(
        session,
        source,
        skill,
        base_date - timedelta(weeks=1),
        skill_share=0.12,
    )
    create_weekly_indicator(
        session,
        source,
        skill,
        base_date,
        skill_share=0.13,
    )

    service = ForecastService(session)
    result = service.forecast_skill_demand("elixir")

    assert isinstance(result, ForecastResult)
    assert result.direction == "stable"


def test_deterministic_reproducible_results(
    session: Session,
) -> None:
    """Test that results are deterministic and reproducible"""
    source = create_source(session, "muse")
    skill = create_skill(session, "kotlin")

    base_date = datetime(2026, 8, 10, tzinfo=UTC)

    create_weekly_indicator(
        session,
        source,
        skill,
        base_date - timedelta(weeks=3),
        skill_share=0.12,
    )
    create_weekly_indicator(
        session,
        source,
        skill,
        base_date - timedelta(weeks=2),
        skill_share=0.15,
    )
    create_weekly_indicator(
        session,
        source,
        skill,
        base_date - timedelta(weeks=1),
        skill_share=0.18,
    )
    create_weekly_indicator(
        session,
        source,
        skill,
        base_date,
        skill_share=0.22,
    )

    service = ForecastService(session)

    result1 = service.forecast_skill_demand("kotlin")
    result2 = service.forecast_skill_demand("kotlin")

    assert isinstance(result1, ForecastResult)
    assert isinstance(result2, ForecastResult)

    assert result1.score == result2.score
    assert result1.direction == result2.direction
    assert result1.confidence == result2.confidence
    assert result1.risk == result2.risk
    assert result1.explanation == result2.explanation
    assert result1.calculation_steps == result2.calculation_steps


def test_risk_levels(session: Session) -> None:
    """Test risk level determination"""
    source = create_source(session, "muse")
    skill = create_skill(session, "go")

    base_date = datetime(2026, 8, 10, tzinfo=UTC)

    create_weekly_indicator(
        session,
        source,
        skill,
        base_date - timedelta(weeks=3),
        skill_share=0.10,
    )
    create_weekly_indicator(
        session,
        source,
        skill,
        base_date - timedelta(weeks=2),
        skill_share=0.12,
    )
    create_weekly_indicator(
        session,
        source,
        skill,
        base_date - timedelta(weeks=1),
        skill_share=0.14,
    )
    create_weekly_indicator(
        session,
        source,
        skill,
        base_date,
        skill_share=0.16,
        coverage_days=7,
        eligible_postings_count=100,
    )

    service = ForecastService(session)
    result = service.forecast_skill_demand("go")

    assert isinstance(result, ForecastResult)
    assert result.risk == "low"


def test_positive_acceleration(session: Session) -> None:
    """Test positive acceleration in trend produces higher scores"""
    source = create_source(session, "muse")
    skill = create_skill(session, "ai")

    base_date = datetime(2026, 8, 10, tzinfo=UTC)

    create_weekly_indicator(
        session,
        source,
        skill,
        base_date - timedelta(weeks=3),
        skill_share=0.10,
    )
    create_weekly_indicator(
        session,
        source,
        skill,
        base_date - timedelta(weeks=2),
        skill_share=0.12,
    )
    create_weekly_indicator(
        session,
        source,
        skill,
        base_date - timedelta(weeks=1),
        skill_share=0.15,
    )
    create_weekly_indicator(
        session,
        source,
        skill,
        base_date,
        skill_share=0.20,
    )

    service = ForecastService(session)
    result = service.forecast_skill_demand("ai")

    assert isinstance(result, ForecastResult)
    assert result.direction == "growing"
    assert "Momentum: +2.0pp" in result.explanation