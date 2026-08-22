"""SQLAlchemy domain models."""

from app.models.data_source import DataSource
from app.models.ingestion_run import IngestionRun
from app.models.job_posting import JobPosting
from app.models.job_skill_match import JobSkillMatch
from app.models.raw_source_record import RawSourceRecord
from app.models.skill import Skill
from app.models.skill_alias import SkillAlias
from app.models.weekly_indicator import WeeklyIndicator

__all__ = [
    "DataSource",
    "IngestionRun",
    "JobPosting",
    "JobSkillMatch",
    "RawSourceRecord",
    "Skill",
    "SkillAlias",
    "WeeklyIndicator",
]
