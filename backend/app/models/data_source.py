from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.ingestion_run import IngestionRun
    from app.models.job_posting import JobPosting
    from app.models.raw_source_record import RawSourceRecord


class DataSource(TimestampMixin, Base):
    __tablename__ = "data_sources"
    __table_args__ = (UniqueConstraint("code", name="uq_data_sources_code"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), index=True)
    name: Mapped[str] = mapped_column(String(255))
    base_url: Mapped[str] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    last_successful_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    ingestion_runs: Mapped[list[IngestionRun]] = relationship(back_populates="source")
    raw_source_records: Mapped[list[RawSourceRecord]] = relationship(back_populates="source")
    job_postings: Mapped[list[JobPosting]] = relationship(back_populates="source")
