from datetime import UTC, datetime, timedelta
from decimal import Decimal

from pydantic import BaseModel, field_validator, model_validator


class WeeklyIndicatorFilters(BaseModel):
    """Optional filters for persisted weekly indicators"""

    source: str | None = None
    skill: str | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None

    @field_validator("period_start", "period_end")
    @classmethod
    def validate_utc_datetime(cls, value: datetime | None) -> datetime | None:
        """Require timezone-aware UTC period filters"""
        if value is None:
            return value
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Datetime filters must be timezone-aware UTC")
        if value.utcoffset() != timedelta(0):
            raise ValueError("Datetime filters must use UTC")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_period_range(self) -> "WeeklyIndicatorFilters":
        """Require an ordered optional period range"""
        if self.period_start is not None and self.period_end is not None:
            if self.period_start > self.period_end:
                raise ValueError("period_start must be before or equal to period_end")
        return self


class IndicatorSourceResponse(BaseModel):
    """Public source information for one indicator"""

    code: str
    name: str


class IndicatorSkillResponse(BaseModel):
    """Public skill information for one indicator"""

    code: str
    display_name: str


class WeeklyIndicatorResponse(BaseModel):
    """Public representation of one persisted weekly indicator"""

    source: IndicatorSourceResponse
    skill: IndicatorSkillResponse
    period_start: datetime
    period_end: datetime
    eligible_postings_count: int
    matching_postings_count: int
    skill_share: Decimal
    coverage_days: int
    calculated_at: datetime

    @field_validator("period_start", "period_end", "calculated_at")
    @classmethod
    def normalize_utc_datetime(cls, value: datetime) -> datetime:
        """Normalize persisted indicator datetimes to UTC"""
        if value.tzinfo is None or value.utcoffset() is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
