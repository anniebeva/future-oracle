from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.data_source import DataSource
    from app.models.skill import Skill


class WeeklyIndicator(Base):
    """Persisted source-level skill metric for one weekly period"""

    __tablename__ = "weekly_indicators"
    __table_args__ = (
        UniqueConstraint(
            "source_id",
            "skill_id",
            "period_start",
            "period_end",
            name="uq_weekly_indicators_source_skill_period",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(
        ForeignKey("data_sources.id", ondelete="RESTRICT"), index=True
    )
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id", ondelete="RESTRICT"), index=True)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    eligible_postings_count: Mapped[int] = mapped_column(Integer)
    matching_postings_count: Mapped[int] = mapped_column(Integer)
    skill_share: Mapped[Decimal] = mapped_column(Numeric(12, 8))
    coverage_days: Mapped[int] = mapped_column(Integer)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    source: Mapped[DataSource] = relationship(back_populates="weekly_indicators")
    skill: Mapped[Skill] = relationship(back_populates="weekly_indicators")
