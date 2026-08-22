"""create weekly indicators

Revision ID: 20260822_0003
Revises: 20260821_0002
Create Date: 2026-08-22 00:00:00

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "20260822_0003"
down_revision: Union[str, Sequence[str], None] = "20260821_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "weekly_indicators",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("skill_id", sa.Integer(), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("eligible_postings_count", sa.Integer(), nullable=False),
        sa.Column("matching_postings_count", sa.Integer(), nullable=False),
        sa.Column("skill_share", sa.Numeric(precision=12, scale=8), nullable=False),
        sa.Column("coverage_days", sa.Integer(), nullable=False),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["source_id"], ["data_sources.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_id",
            "skill_id",
            "period_start",
            "period_end",
            name="uq_weekly_indicators_source_skill_period",
        ),
    )
    op.create_index("ix_weekly_indicators_source_id", "weekly_indicators", ["source_id"])
    op.create_index("ix_weekly_indicators_skill_id", "weekly_indicators", ["skill_id"])
    op.create_index("ix_weekly_indicators_period_start", "weekly_indicators", ["period_start"])
    op.create_index("ix_weekly_indicators_period_end", "weekly_indicators", ["period_end"])


def downgrade() -> None:
    op.drop_index("ix_weekly_indicators_period_end", table_name="weekly_indicators")
    op.drop_index("ix_weekly_indicators_period_start", table_name="weekly_indicators")
    op.drop_index("ix_weekly_indicators_skill_id", table_name="weekly_indicators")
    op.drop_index("ix_weekly_indicators_source_id", table_name="weekly_indicators")
    op.drop_table("weekly_indicators")
