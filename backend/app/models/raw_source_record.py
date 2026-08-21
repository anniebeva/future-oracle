from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.data_source import DataSource
    from app.models.ingestion_run import IngestionRun


class RawSourceRecord(TimestampMixin, Base):
    __tablename__ = "raw_source_records"
    __table_args__ = (
        Index(
            "ix_raw_source_records_source_external_retrieved_at",
            "source_id",
            "external_id",
            "retrieved_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    ingestion_run_id: Mapped[int] = mapped_column(
        ForeignKey("ingestion_runs.id", ondelete="RESTRICT"), index=True
    )
    source_id: Mapped[int] = mapped_column(
        ForeignKey("data_sources.id", ondelete="RESTRICT"), index=True
    )
    external_id: Mapped[str] = mapped_column(String(255))
    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)
    payload_hash: Mapped[str] = mapped_column(String(64), index=True)

    source: Mapped[DataSource] = relationship(back_populates="raw_source_records")
    ingestion_run: Mapped[IngestionRun] = relationship(back_populates="raw_source_records")
