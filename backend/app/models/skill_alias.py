from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.skill import Skill


class SkillAlias(TimestampMixin, Base):
    __tablename__ = "skill_aliases"
    __table_args__ = (UniqueConstraint("skill_id", "alias", name="uq_skill_aliases_skill_alias"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), index=True)
    alias: Mapped[str] = mapped_column(String(255))
    match_type: Mapped[str] = mapped_column(String(30), default="word", server_default="word")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    skill: Mapped[Skill] = relationship(back_populates="aliases")
