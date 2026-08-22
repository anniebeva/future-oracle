from datetime import datetime

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.data_source import DataSource
from app.models.skill import Skill
from app.models.weekly_indicator import WeeklyIndicator


class WeeklyIndicatorRepository:
    """Read persisted weekly indicators with their source and skill"""

    def list_indicators(
        self,
        session: Session,
        *,
        source: str | None = None,
        skill: str | None = None,
        period_start: datetime | None = None,
        period_end: datetime | None = None,
    ) -> list[tuple[WeeklyIndicator, DataSource, Skill]]:
        """Return active-source and active-skill indicators matching filters"""
        statement: Select[tuple[WeeklyIndicator, DataSource, Skill]] = (
            select(WeeklyIndicator, DataSource, Skill)
            .join(DataSource, WeeklyIndicator.source_id == DataSource.id)
            .join(Skill, WeeklyIndicator.skill_id == Skill.id)
            .where(DataSource.is_active.is_(True), Skill.is_active.is_(True))
            .order_by(
                WeeklyIndicator.period_start.desc(),
                WeeklyIndicator.period_end.desc(),
                DataSource.code,
                Skill.code,
            )
        )
        if source is not None:
            statement = statement.where(DataSource.code == source)
        if skill is not None:
            statement = statement.where(Skill.code == skill)
        if period_start is not None:
            statement = statement.where(WeeklyIndicator.period_start >= period_start)
        if period_end is not None:
            statement = statement.where(WeeklyIndicator.period_end <= period_end)
        return list(session.execute(statement).tuples())
