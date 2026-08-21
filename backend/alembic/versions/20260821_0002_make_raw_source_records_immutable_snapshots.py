"""make raw source records immutable snapshots

Revision ID: 20260821_0002
Revises: 20260821_0001
Create Date: 2026-08-21 00:10:00

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "20260821_0002"
down_revision: Union[str, Sequence[str], None] = "20260821_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "uq_raw_source_records_source_external",
        "raw_source_records",
        type_="unique",
    )
    op.create_index(
        "ix_raw_source_records_source_external_retrieved_at",
        "raw_source_records",
        ["source_id", "external_id", "retrieved_at"],
        unique=False,
    )

    op.drop_constraint(
        "job_postings_raw_source_record_id_fkey",
        "job_postings",
        type_="foreignkey",
    )
    op.drop_constraint(
        "job_postings_raw_source_record_id_key",
        "job_postings",
        type_="unique",
    )
    op.drop_column("job_postings", "raw_source_record_id")


def downgrade() -> None:
    op.add_column(
        "job_postings",
        sa.Column("raw_source_record_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "job_postings_raw_source_record_id_fkey",
        "job_postings",
        "raw_source_records",
        ["raw_source_record_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_unique_constraint(
        "job_postings_raw_source_record_id_key",
        "job_postings",
        ["raw_source_record_id"],
    )

    op.drop_index(
        "ix_raw_source_records_source_external_retrieved_at",
        table_name="raw_source_records",
    )
    op.create_unique_constraint(
        "uq_raw_source_records_source_external",
        "raw_source_records",
        ["source_id", "external_id"],
    )
