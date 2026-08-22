from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.data_source import DataSource
from app.models.skill import Skill


class ReferenceRepository:
    """Read active source and skill reference data"""

    def list_sources(self, session: Session) -> list[DataSource]:
        """Return active sources ordered by code"""
        return list(
            session.scalars(
                select(DataSource).where(DataSource.is_active.is_(True)).order_by(DataSource.code)
            )
        )

    def list_skills(self, session: Session) -> list[Skill]:
        """Return active skills ordered by code"""
        return list(
            session.scalars(select(Skill).where(Skill.is_active.is_(True)).order_by(Skill.code))
        )
