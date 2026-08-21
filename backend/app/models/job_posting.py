from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.data_source import DataSource
    from app.models.job_skill_match import JobSkillMatch


class JobPosting(TimestampMixin, Base):
    __tablename__ = "job_postings"
    __table_args__ = (
        UniqueConstraint("source_id", "external_id", name="uq_job_postings_source_external"),
        Index("ix_job_postings_source_published_at", "source_id", "published_at"),
        Index("ix_job_postings_source_active", "source_id", "is_active"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(
        ForeignKey("data_sources.id", ondelete="RESTRICT"), index=True
    )
    external_id: Mapped[str] = mapped_column(String(255))
    source_url: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(String(500), index=True)
    company_name: Mapped[str | None] = mapped_column(String(255))
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    location_raw: Mapped[str | None] = mapped_column(String(500))
    location_scope: Mapped[str | None] = mapped_column(String(100), index=True)
    is_remote: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    category: Mapped[str | None] = mapped_column(String(255), index=True)
    employment_type: Mapped[str | None] = mapped_column(String(100))
    description_html: Mapped[str | None] = mapped_column(Text)
    description_text: Mapped[str | None] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    source: Mapped[DataSource] = relationship(back_populates="job_postings")
    skill_matches: Mapped[list[JobSkillMatch]] = relationship(back_populates="job_posting")
