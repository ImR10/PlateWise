"""Schema-level tests: tables/enums exist, and migrations succeed from empty."""

from __future__ import annotations

import uuid

import conftest
import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine, make_url

from alembic import command
from app.db.base import Base

EXPECTED_TABLES = {
    "institutions",
    "venues",
    "stations",
    "menu_items",
    "menu_item_aliases",
    "nutrition_facts",
    "ingredients",
    "menu_item_ingredients",
    "allergens",
    "menu_item_allergens",
    "dietary_tags",
    "menu_item_dietary_tags",
    "menu_offerings",
    "offering_reports",
    "menu_item_suggestions",
    "data_imports",
}

EXPECTED_ENUMS = {
    "institution_type",
    "venue_type",
    "alias_source_type",
    "allergen_declaration_type",
    "allergen_source_type",
    "dietary_tag_source_type",
    "nutrition_source_type",
    "meal_period",
    "offering_status",
    "offering_source_type",
    "report_type",
    "moderation_status",
    "suggestion_status",
    "import_source_type",
    "import_status",
}


def test_metadata_matches_expected_tables() -> None:
    """The ORM metadata declares exactly the MVP table set."""
    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_all_tables_created(engine: Engine) -> None:
    """Every expected table exists in the migrated database."""
    tables = set(inspect(engine).get_table_names())
    assert EXPECTED_TABLES <= tables


def test_alembic_at_head(engine: Engine) -> None:
    with engine.connect() as conn:
        version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
    assert version == "20260718_0001"


def test_enum_types_created(engine: Engine) -> None:
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT typname FROM pg_type WHERE typtype = 'e'")).scalars().all()
    assert EXPECTED_ENUMS <= set(rows)


def test_partial_and_special_constraints_present(engine: Engine) -> None:
    """Spot-check the non-trivial indexes/constraints made it into the schema."""
    inspector = inspect(engine)

    # Partial unique index enforcing one active nutrition record per item.
    nutrition_indexes = {ix["name"] for ix in inspector.get_indexes("nutrition_facts")}
    assert "uq_nutrition_facts_active_per_menu_item" in nutrition_indexes

    # Partial unique index enforcing one active report per reporter/category.
    report_indexes = {ix["name"] for ix in inspector.get_indexes("offering_reports")}
    assert "uq_offering_reports_active_reporter_category" in report_indexes

    # Confidence check constraint on dietary-tag links.
    checks = {c["name"] for c in inspector.get_check_constraints("menu_item_dietary_tags")}
    assert "ck_menu_item_dietary_tags_confidence_range" in checks


def test_migration_upgrade_downgrade_roundtrip(database_url: str) -> None:
    """A full upgrade->downgrade cycle succeeds on a fresh, empty database."""
    base_url = make_url(database_url)
    scratch_name = f"platewise_mig_{uuid.uuid4().hex[:12]}"
    scratch_url = base_url.set(database=scratch_name).render_as_string(hide_password=False)

    conftest._ensure_database_exists(scratch_url)
    scratch_engine = create_engine(scratch_url)
    try:
        cfg = conftest._alembic_config(scratch_url)

        command.upgrade(cfg, "head")
        tables = set(inspect(scratch_engine).get_table_names())
        assert EXPECTED_TABLES <= tables

        command.downgrade(cfg, "base")
        remaining = set(inspect(scratch_engine).get_table_names())
        # Only Alembic's own bookkeeping table may remain.
        assert not (EXPECTED_TABLES & remaining)
        with scratch_engine.connect() as conn:
            enum_count = conn.execute(
                text("SELECT count(*) FROM pg_type WHERE typtype = 'e'")
            ).scalar()
        assert enum_count == 0
    finally:
        scratch_engine.dispose()
        # Drop the scratch database from a maintenance connection.
        maint = create_engine(
            base_url.set(database="postgres"), isolation_level="AUTOCOMMIT"
        )
        try:
            with maint.connect() as conn:
                conn.execute(text(f'DROP DATABASE IF EXISTS "{scratch_name}"'))
        finally:
            maint.dispose()


@pytest.mark.parametrize("table", sorted(EXPECTED_TABLES))
def test_every_table_has_uuid_primary_key(engine: Engine, table: str) -> None:
    pk = inspect(engine).get_pk_constraint(table)
    assert pk["constrained_columns"] == ["id"]
