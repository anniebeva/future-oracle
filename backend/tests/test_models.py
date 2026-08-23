from sqlalchemy import Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base import Base
from app.models import (JobPosting, JobSkillMatch, RawSourceRecord, SkillAlias,
                        WeeklyIndicator)


def unique_constraint_columns(table_name: str) -> set[tuple[str, ...]]:
    table = Base.metadata.tables[table_name]
    return {
        tuple(column.name for column in constraint.columns)
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }


def test_requested_unique_constraints_are_declared() -> None:
    assert ("code",) in unique_constraint_columns("data_sources")
    assert ("source_id", "external_id") in unique_constraint_columns("job_postings")
    assert ("code",) in unique_constraint_columns("skills")
    assert ("skill_id", "alias") in unique_constraint_columns("skill_aliases")
    assert (
        "job_posting_id",
        "skill_id",
        "dictionary_version",
    ) in unique_constraint_columns("job_skill_matches")


def test_raw_payload_uses_postgresql_jsonb() -> None:
    payload_column = RawSourceRecord.__table__.c.payload

    assert isinstance(payload_column.type, JSONB)


def test_relationship_foreign_keys_are_declared() -> None:
    assert JobPosting.__table__.c.source_id.foreign_keys
    assert SkillAlias.__table__.c.skill_id.foreign_keys
    assert JobSkillMatch.__table__.c.job_posting_id.foreign_keys
    assert JobSkillMatch.__table__.c.skill_id.foreign_keys


def test_raw_source_records_allow_multiple_snapshots_for_one_source_posting() -> None:
    assert ("source_id", "external_id") not in unique_constraint_columns(
        "raw_source_records"
    )


def test_job_postings_do_not_reference_a_single_raw_snapshot() -> None:
    assert "raw_source_record_id" not in JobPosting.__table__.c


def test_weekly_indicator_is_registered_with_required_columns() -> None:
    table = Base.metadata.tables["weekly_indicators"]

    assert WeeklyIndicator.__table__ is table
    assert {
        "id",
        "source_id",
        "skill_id",
        "period_start",
        "period_end",
        "eligible_postings_count",
        "matching_postings_count",
        "skill_share",
        "coverage_days",
        "calculated_at",
    }.issubset(table.c.keys())


def test_weekly_indicator_constraints_and_numeric_share_are_declared() -> None:
    table = WeeklyIndicator.__table__

    assert table.c.source_id.foreign_keys
    assert table.c.skill_id.foreign_keys
    assert (
        "source_id",
        "skill_id",
        "period_start",
        "period_end",
    ) in unique_constraint_columns("weekly_indicators")
    assert isinstance(table.c.skill_share.type, Numeric)
    assert table.c.period_start.type.timezone is True
    assert table.c.period_end.type.timezone is True
    assert table.c.calculated_at.type.timezone is True
