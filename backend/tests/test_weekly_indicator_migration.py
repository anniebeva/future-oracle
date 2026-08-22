from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType
from unittest.mock import Mock

from sqlalchemy import Column, MetaData, Numeric, Table, UniqueConstraint


def load_migration() -> ModuleType:
    migration_path = (
        Path(__file__).parents[1]
        / "alembic"
        / "versions"
        / "20260822_0003_create_weekly_indicators.py"
    )
    spec = spec_from_file_location("weekly_indicator_migration", migration_path)
    assert spec is not None
    assert spec.loader is not None
    migration = module_from_spec(spec)
    spec.loader.exec_module(migration)
    return migration


def test_weekly_indicator_migration_creates_expected_schema(monkeypatch) -> None:
    migration = load_migration()
    create_table = Mock()
    create_index = Mock()
    monkeypatch.setattr(migration.op, "create_table", create_table)
    monkeypatch.setattr(migration.op, "create_index", create_index)

    migration.upgrade()

    assert migration.down_revision == "20260821_0002"
    assert create_table.call_args.args[0] == "weekly_indicators"
    table = Table("weekly_indicators", MetaData(), *create_table.call_args.args[1:])
    columns = {item.name for item in table.c if isinstance(item, Column)}
    unique_constraints = [
        constraint for constraint in table.constraints if isinstance(constraint, UniqueConstraint)
    ]

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
    } == columns
    assert {
        foreign_key.elements[0].target_fullname for foreign_key in table.foreign_key_constraints
    } == {
        "data_sources.id",
        "skills.id",
    }
    assert [
        tuple(column.name for column in constraint.columns) for constraint in unique_constraints
    ] == [("source_id", "skill_id", "period_start", "period_end")]
    assert isinstance(table.c.skill_share.type, Numeric)
    assert {call.args[0] for call in create_index.call_args_list} == {
        "ix_weekly_indicators_source_id",
        "ix_weekly_indicators_skill_id",
        "ix_weekly_indicators_period_start",
        "ix_weekly_indicators_period_end",
    }
