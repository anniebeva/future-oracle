from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.data_source import DataSource
    from app.models.raw_source_record import RawSourceRecord


class IngestionRun(TimestampMixin, Base):
    __tablename__ = "ingestion_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(
        ForeignKey("data_sources.id", ondelete="RESTRICT"), index=True
    )
    status: Mapped[str] = mapped_column(String(30), index=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    records_received: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0"
    )
    error_message: Mapped[str | None] = mapped_column(Text)

    source: Mapped[DataSource] = relationship(back_populates="ingestion_runs")
    raw_source_records: Mapped[list[RawSourceRecord]] = relationship(
        back_populates="ingestion_run"
    )
