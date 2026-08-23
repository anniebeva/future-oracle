from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.job_posting import JobPosting
    from app.models.skill import Skill


class JobSkillMatch(TimestampMixin, Base):
    __tablename__ = "job_skill_matches"
    __table_args__ = (
        UniqueConstraint(
            "job_posting_id",
            "skill_id",
            "dictionary_version",
            name="uq_job_skill_matches_posting_skill_version",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    job_posting_id: Mapped[int] = mapped_column(
        ForeignKey("job_postings.id", ondelete="CASCADE"), index=True
    )
    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skills.id", ondelete="RESTRICT"), index=True
    )
    dictionary_version: Mapped[int] = mapped_column(Integer)
    matched_alias: Mapped[str] = mapped_column(String(255))
    matched_in_title: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    matched_in_description: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    match_count: Mapped[int] = mapped_column(Integer, default=1, server_default="1")

    job_posting: Mapped[JobPosting] = relationship(back_populates="skill_matches")
    skill: Mapped[Skill] = relationship(back_populates="job_skill_matches")
