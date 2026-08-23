from datetime import UTC, datetime, timedelta

from pydantic import BaseModel, field_validator, model_validator


class JobPostingFilters(BaseModel):
    """Optional filters for public job postings"""

    source: str | None = None
    skill: str | None = None
    location: str | None = None
    is_remote: bool | None = None
    published_from: datetime | None = None
    published_to: datetime | None = None
    search: str | None = None

    @field_validator("published_from", "published_to")
    @classmethod
    def validate_utc_datetime(cls, value: datetime | None) -> datetime | None:
        """Require timezone-aware UTC publication filters"""
        if value is None:
            return value
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Publication filters must be timezone-aware UTC")
        if value.utcoffset() != timedelta(0):
            raise ValueError("Publication filters must use UTC")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_publication_range(self) -> "JobPostingFilters":
        """Require an ordered optional publication range"""
        if self.published_from is not None and self.published_to is not None:
            if self.published_from > self.published_to:
                raise ValueError(
                    "published_from must be before or equal to published_to"
                )
        return self


class JobSourceResponse(BaseModel):
    """Public source information for one job posting"""

    code: str
    name: str


class JobSkillResponse(BaseModel):
    """Public skill information matched to one job posting"""

    code: str
    display_name: str


class JobPostingResponse(BaseModel):
    """Public representation of one active job posting"""

    id: int
    source: JobSourceResponse
    external_id: str
    title: str
    company_name: str | None
    source_url: str
    published_at: datetime
    location_raw: str | None
    location_scope: str | None
    is_remote: bool
    category: str | None
    employment_type: str | None
    description_text: str | None
    skills: list[JobSkillResponse]

    @field_validator("published_at")
    @classmethod
    def normalize_utc_datetime(cls, value: datetime) -> datetime:
        """Normalize persisted publication datetimes to UTC"""
        if value.tzinfo is None or value.utcoffset() is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
