from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.job_skill_match import JobSkillMatch
    from app.models.skill_alias import SkillAlias


class Skill(TimestampMixin, Base):
    __tablename__ = "skills"
    __table_args__ = (UniqueConstraint("code", name="uq_skills_code"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), index=True)
    display_name: Mapped[str] = mapped_column(String(100))
    dictionary_version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    aliases: Mapped[list[SkillAlias]] = relationship(back_populates="skill")
    job_skill_matches: Mapped[list[JobSkillMatch]] = relationship(back_populates="skill")
