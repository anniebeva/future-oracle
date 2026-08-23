from datetime import datetime

from sqlalchemy import Select, exists, func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.data_source import DataSource
from app.models.job_posting import JobPosting
from app.models.job_skill_match import JobSkillMatch
from app.models.skill import Skill


class JobPostingRepository:
    """Read active job postings with source and skill relationships"""

    def list_postings(
        self,
        session: Session,
        *,
        source: str | None = None,
        skill: str | None = None,
        location: str | None = None,
        is_remote: bool | None = None,
        published_from: datetime | None = None,
        published_to: datetime | None = None,
        search: str | None = None,
    ) -> list[JobPosting]:
        """Return active postings matching optional public filters"""
        statement: Select[tuple[JobPosting]] = (
            select(JobPosting)
            .join(DataSource, JobPosting.source_id == DataSource.id)
            .options(
                joinedload(JobPosting.source),
                selectinload(JobPosting.skill_matches).joinedload(JobSkillMatch.skill),
            )
            .where(JobPosting.is_active.is_(True), DataSource.is_active.is_(True))
            .order_by(JobPosting.published_at.desc(), JobPosting.id.desc())
        )
        if source is not None:
            statement = statement.where(DataSource.code == source)
        if skill is not None:
            statement = statement.where(self._current_skill_match_exists(skill))
        if location is not None:
            location_pattern = f"%{location.casefold()}%"
            statement = statement.where(
                or_(
                    func.lower(JobPosting.location_raw).like(location_pattern),
                    func.lower(JobPosting.location_scope).like(location_pattern),
                )
            )
        if is_remote is not None:
            statement = statement.where(JobPosting.is_remote.is_(is_remote))
        if published_from is not None:
            statement = statement.where(JobPosting.published_at >= published_from)
        if published_to is not None:
            statement = statement.where(JobPosting.published_at <= published_to)
        if search is not None:
            statement = statement.where(
                func.lower(JobPosting.title).like(f"%{search.casefold()}%")
            )
        return list(session.scalars(statement).unique())

    @staticmethod
    def _current_skill_match_exists(skill_code: str):
        """Match a posting to one skill at its current dictionary version"""
        return exists(
            select(1)
            .select_from(JobSkillMatch)
            .join(Skill, JobSkillMatch.skill_id == Skill.id)
            .where(
                JobSkillMatch.job_posting_id == JobPosting.id,
                JobSkillMatch.dictionary_version == Skill.dictionary_version,
                Skill.code == skill_code,
                Skill.is_active.is_(True),
            )
        )
