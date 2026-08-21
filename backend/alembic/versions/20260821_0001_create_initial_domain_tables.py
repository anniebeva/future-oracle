"""create initial domain tables

Revision ID: 20260821_0001
Revises:
Create Date: 2026-08-21 00:00:00

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260821_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "data_sources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("base_url", sa.String(length=500), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("last_successful_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_data_sources_code"),
    )
    op.create_index(op.f("ix_data_sources_code"), "data_sources", ["code"], unique=False)

    op.create_table(
        "skills",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column("dictionary_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_skills_code"),
    )
    op.create_index(op.f("ix_skills_code"), "skills", ["code"], unique=False)

    op.create_table(
        "ingestion_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("records_received", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["source_id"], ["data_sources.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_ingestion_runs_source_id"), "ingestion_runs", ["source_id"], unique=False
    )
    op.create_index(op.f("ix_ingestion_runs_status"), "ingestion_runs", ["status"], unique=False)

    op.create_table(
        "raw_source_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ingestion_run_id", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column(
            "retrieved_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["ingestion_run_id"], ["ingestion_runs.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["source_id"], ["data_sources.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_id", "external_id", name="uq_raw_source_records_source_external"
        ),
    )
    op.create_index(
        op.f("ix_raw_source_records_ingestion_run_id"),
        "raw_source_records",
        ["ingestion_run_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_raw_source_records_payload_hash"),
        "raw_source_records",
        ["payload_hash"],
        unique=False,
    )
    op.create_index(
        op.f("ix_raw_source_records_source_id"), "raw_source_records", ["source_id"], unique=False
    )

    op.create_table(
        "job_postings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("raw_source_record_id", sa.Integer(), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "first_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("location_raw", sa.String(length=500), nullable=True),
        sa.Column("location_scope", sa.String(length=100), nullable=True),
        sa.Column("is_remote", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("category", sa.String(length=255), nullable=True),
        sa.Column("employment_type", sa.String(length=100), nullable=True),
        sa.Column("description_html", sa.Text(), nullable=True),
        sa.Column("description_text", sa.Text(), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["raw_source_record_id"], ["raw_source_records.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["source_id"], ["data_sources.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("raw_source_record_id"),
        sa.UniqueConstraint("source_id", "external_id", name="uq_job_postings_source_external"),
    )
    op.create_index(op.f("ix_job_postings_category"), "job_postings", ["category"], unique=False)
    op.create_index(
        op.f("ix_job_postings_content_hash"), "job_postings", ["content_hash"], unique=False
    )
    op.create_index(
        op.f("ix_job_postings_location_scope"), "job_postings", ["location_scope"], unique=False
    )
    op.create_index(
        op.f("ix_job_postings_published_at"), "job_postings", ["published_at"], unique=False
    )
    op.create_index(
        op.f("ix_job_postings_source_active"),
        "job_postings",
        ["source_id", "is_active"],
        unique=False,
    )
    op.create_index(op.f("ix_job_postings_source_id"), "job_postings", ["source_id"], unique=False)
    op.create_index(
        op.f("ix_job_postings_source_published_at"),
        "job_postings",
        ["source_id", "published_at"],
        unique=False,
    )
    op.create_index(op.f("ix_job_postings_title"), "job_postings", ["title"], unique=False)

    op.create_table(
        "skill_aliases",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("skill_id", sa.Integer(), nullable=False),
        sa.Column("alias", sa.String(length=255), nullable=False),
        sa.Column("match_type", sa.String(length=30), server_default="word", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("skill_id", "alias", name="uq_skill_aliases_skill_alias"),
    )
    op.create_index(op.f("ix_skill_aliases_skill_id"), "skill_aliases", ["skill_id"], unique=False)

    op.create_table(
        "job_skill_matches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_posting_id", sa.Integer(), nullable=False),
        sa.Column("skill_id", sa.Integer(), nullable=False),
        sa.Column("dictionary_version", sa.Integer(), nullable=False),
        sa.Column("matched_alias", sa.String(length=255), nullable=False),
        sa.Column("matched_in_title", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("matched_in_description", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("match_count", sa.Integer(), server_default="1", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["job_posting_id"], ["job_postings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "job_posting_id",
            "skill_id",
            "dictionary_version",
            name="uq_job_skill_matches_posting_skill_version",
        ),
    )
    op.create_index(
        op.f("ix_job_skill_matches_job_posting_id"),
        "job_skill_matches",
        ["job_posting_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_job_skill_matches_skill_id"), "job_skill_matches", ["skill_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_job_skill_matches_skill_id"), table_name="job_skill_matches")
    op.drop_index(op.f("ix_job_skill_matches_job_posting_id"), table_name="job_skill_matches")
    op.drop_table("job_skill_matches")
    op.drop_index(op.f("ix_skill_aliases_skill_id"), table_name="skill_aliases")
    op.drop_table("skill_aliases")
    op.drop_index(op.f("ix_job_postings_title"), table_name="job_postings")
    op.drop_index(op.f("ix_job_postings_source_published_at"), table_name="job_postings")
    op.drop_index(op.f("ix_job_postings_source_id"), table_name="job_postings")
    op.drop_index(op.f("ix_job_postings_source_active"), table_name="job_postings")
    op.drop_index(op.f("ix_job_postings_published_at"), table_name="job_postings")
    op.drop_index(op.f("ix_job_postings_location_scope"), table_name="job_postings")
    op.drop_index(op.f("ix_job_postings_content_hash"), table_name="job_postings")
    op.drop_index(op.f("ix_job_postings_category"), table_name="job_postings")
    op.drop_table("job_postings")
    op.drop_index(op.f("ix_raw_source_records_source_id"), table_name="raw_source_records")
    op.drop_index(op.f("ix_raw_source_records_payload_hash"), table_name="raw_source_records")
    op.drop_index(op.f("ix_raw_source_records_ingestion_run_id"), table_name="raw_source_records")
    op.drop_table("raw_source_records")
    op.drop_index(op.f("ix_ingestion_runs_status"), table_name="ingestion_runs")
    op.drop_index(op.f("ix_ingestion_runs_source_id"), table_name="ingestion_runs")
    op.drop_table("ingestion_runs")
    op.drop_index(op.f("ix_skills_code"), table_name="skills")
    op.drop_table("skills")
    op.drop_index(op.f("ix_data_sources_code"), table_name="data_sources")
    op.drop_table("data_sources")
