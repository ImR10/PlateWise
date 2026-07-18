"""End-to-end import service tests: persistence, provenance, idempotency, safety."""

from __future__ import annotations

from decimal import Decimal

import import_fixtures as fx
import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

import app.imports.repositories as repo
from app.db.enums import (
    CalculationStatus,
    ImportErrorSeverity,
    ImportErrorStage,
    ImportStatus,
    NutritionProvenance,
    NutritionReviewStatus,
)
from app.db.models import (
    DataImport,
    DataImportError,
    MenuItem,
    MenuOffering,
    NutritionFacts,
    RecipeIngredient,
    RecipeVersion,
    Station,
    Venue,
)


def _count(session: Session, model) -> int:
    return int(session.scalar(select(func.count()).select_from(model)) or 0)


def _item(session: Session, external_id: str) -> MenuItem | None:
    return session.scalar(select(MenuItem).where(MenuItem.external_id == external_id))


def _calc(item: MenuItem) -> list[NutritionFacts]:
    return [
        f for f in item.active_nutrition if f.provenance == NutritionProvenance.RECIPE_CALCULATED
    ]


# --- Source-provided nutrition -------------------------------------------


def test_source_nutrition_persisted(db_session: Session) -> None:
    result = fx.run(db_session, fx.fixture_1_source_nutrition())
    assert result.status == ImportStatus.COMPLETED
    assert result.counters.created == 1
    assert result.counters.nutrition_provided == 1

    item = _item(db_session, "item-chicken")
    assert item is not None
    facts = item.active_nutrition
    assert len(facts) == 1
    assert facts[0].provenance == NutritionProvenance.SOURCE_PROVIDED
    assert facts[0].calories == Decimal("240.00")
    # A nutrient absent from the source stays NULL (never zero).
    assert facts[0].fiber_g is None


def test_source_nutrition_import_is_idempotent(db_session: Session) -> None:
    fx.run(db_session, fx.fixture_1_source_nutrition())
    second = fx.run(db_session, fx.fixture_1_source_nutrition())
    assert second.counters.created == 0
    assert second.counters.unchanged == 1
    assert second.counters.nutrition_provided == 0
    assert _count(db_session, MenuItem) == 1
    assert _count(db_session, NutritionFacts) == 1


# --- Recipe-based nutrition ----------------------------------------------


def test_recipe_import_calculates_and_persists(db_session: Session) -> None:
    result = fx.run(db_session, fx.fixture_2_resolvable_recipe())
    assert result.status == ImportStatus.COMPLETED
    assert result.counters.nutrition_calculated == 1
    assert result.counters.ingredients_resolved == 3

    item = _item(db_session, "item-chicken-rice")
    assert item is not None
    calc = _calc(item)
    assert len(calc) == 1
    assert calc[0].is_complete
    assert calc[0].calculation_status == CalculationStatus.COMPLETE
    assert calc[0].recipe_version_id is not None

    # Portion conversion used the resolved provider weight (rice: 1 cup = 158 g).
    rice = db_session.scalar(
        select(RecipeIngredient).where(RecipeIngredient.line_no == 3)
    )
    assert rice is not None and rice.grams == Decimal("158.0000")


def test_recipe_import_is_idempotent(db_session: Session) -> None:
    fx.run(db_session, fx.fixture_2_resolvable_recipe())
    second = fx.run(db_session, fx.fixture_8_repeat())
    assert second.counters.nutrition_calculated == 0
    assert _count(db_session, MenuItem) == 1
    assert _count(db_session, RecipeVersion) == 1
    assert _count(db_session, RecipeIngredient) == 3
    assert _count(db_session, NutritionFacts) == 1


def test_recipe_update_creates_new_version_preserving_history(db_session: Session) -> None:
    fx.run(db_session, fx.fixture_2_resolvable_recipe())
    changed = fx.fixture_2_resolvable_recipe()
    # Change the chicken quantity -> new recipe content -> new version.
    changed["menu_items"][0]["recipe"]["ingredients"][0]["quantity"] = "8"
    changed["menu_items"][0]["recipe"]["ingredients"][0]["original_text"] = "8 oz chicken breast"
    result = fx.run(db_session, changed)
    assert result.counters.nutrition_calculated == 1

    versions = db_session.scalars(select(RecipeVersion)).all()
    assert len(versions) == 2  # history preserved
    active = [v for v in versions if v.valid_until is None]
    assert len(active) == 1 and active[0].version_no == 2

    item = _item(db_session, "item-chicken-rice")
    assert item is not None
    calc = _calc(item)
    assert len(calc) == 1 and calc[0].recipe_version_id == active[0].id


# --- Coexistence & precedence --------------------------------------------


def test_source_and_calculated_nutrition_coexist(db_session: Session) -> None:
    fx.run(db_session, fx.fixture_9_both_nutrition())
    item = _item(db_session, "item-both")
    assert item is not None
    provenances = {f.provenance for f in item.active_nutrition}
    assert provenances == {
        NutritionProvenance.SOURCE_PROVIDED,
        NutritionProvenance.RECIPE_CALCULATED,
    }


def test_display_prefers_source_provided(db_session: Session) -> None:
    fx.run(db_session, fx.fixture_9_both_nutrition())
    item = _item(db_session, "item-both")
    assert item is not None
    chosen = item.display_nutrition()
    assert chosen is not None
    assert chosen.provenance == NutritionProvenance.SOURCE_PROVIDED


def test_display_falls_back_to_complete_calculated(db_session: Session) -> None:
    fx.run(db_session, fx.fixture_2_resolvable_recipe())
    item = _item(db_session, "item-chicken-rice")
    assert item is not None
    chosen = item.display_nutrition()
    assert chosen is not None
    assert chosen.provenance == NutritionProvenance.RECIPE_CALCULATED


# --- Incomplete / review states ------------------------------------------


def test_unresolved_ingredient_prevents_authoritative_nutrition(db_session: Session) -> None:
    result = fx.run(db_session, fx.fixture_4_unresolved_ingredient())
    assert result.counters.ingredients_unresolved == 1
    item = _item(db_session, "item-unresolved")
    assert item is not None
    calc = _calc(item)
    assert len(calc) == 1
    assert not calc[0].is_complete
    assert calc[0].calculation_status == CalculationStatus.PARTIAL
    assert calc[0].review_status == NutritionReviewStatus.NEEDS_REVIEW
    # No authoritative nutrition available for display.
    assert item.display_nutrition() is None


def test_missing_yield_prevents_complete_calculation(db_session: Session) -> None:
    fx.run(db_session, fx.fixture_6_missing_yield())
    item = _item(db_session, "item-noyield")
    assert item is not None
    calc = _calc(item)
    assert len(calc) == 1
    assert calc[0].calculation_status == CalculationStatus.FAILED
    assert not calc[0].is_complete


def test_vague_quantity_flags_review(db_session: Session) -> None:
    result = fx.run(db_session, fx.fixture_3_vague_quantity())
    assert result.counters.ingredients_unresolved == 1
    item = _item(db_session, "item-vague")
    assert item is not None
    calc = _calc(item)
    assert len(calc) == 1 and not calc[0].is_complete


# --- Malformed / empty / errors ------------------------------------------


def test_malformed_record_is_skipped_not_fatal(db_session: Session) -> None:
    result = fx.run(db_session, fx.fixture_7_malformed_record())
    assert result.status == ImportStatus.COMPLETED_WITH_ERRORS
    assert result.counters.failed == 1
    # The valid record still imported.
    assert _item(db_session, "item-ok") is not None
    errors = db_session.scalars(
        select(DataImportError).where(DataImportError.code == "malformed_record")
    ).all()
    assert len(errors) == 1
    assert errors[0].stage == ImportErrorStage.VALIDATE


def test_empty_payload_is_non_destructive(db_session: Session) -> None:
    fx.run(db_session, fx.fixture_2_resolvable_recipe())
    before = _count(db_session, MenuItem)
    assert before == 1
    result = fx.run(db_session, fx.fixture_10_empty())
    assert result.status == ImportStatus.COMPLETED
    assert result.counters.created == 0
    # Nothing deleted by a suspiciously empty response.
    assert _count(db_session, MenuItem) == before


def test_structured_errors_link_to_run(db_session: Session) -> None:
    result = fx.run(db_session, fx.fixture_4_unresolved_ingredient())
    errors = db_session.scalars(
        select(DataImportError).where(DataImportError.data_import_id == result.import_id)
    ).all()
    assert errors
    resolve_errors = [e for e in errors if e.stage == ImportErrorStage.RESOLVE_INGREDIENT]
    assert resolve_errors
    assert resolve_errors[0].severity == ImportErrorSeverity.WARNING
    assert resolve_errors[0].ingredient_context is not None


def test_failed_record_rolls_back_its_domain_writes(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = repo.upsert_source_nutrition

    def boom(session, menu_item, normalized, import_run):
        if menu_item.external_id == "item-bad-nutri":
            raise RuntimeError("simulated persistence failure")
        return original(session, menu_item, normalized, import_run)

    monkeypatch.setattr(repo, "upsert_source_nutrition", boom)

    payload = {
        "institution": fx.INSTITUTION,
        "menu_items": [
            {
                "source_system": "fixture",
                "external_id": "item-good-nutri",
                "name": "Good",
                "provided_nutrition": {
                    "serving_size": "1", "serving_unit": "each",
                    "nutrients": {"calories": "100"},
                },
            },
            {
                "source_system": "fixture",
                "external_id": "item-bad-nutri",
                "name": "Bad",
                "provided_nutrition": {
                    "serving_size": "1", "serving_unit": "each",
                    "nutrients": {"calories": "200"},
                },
            },
        ],
    }
    result = fx.run(db_session, payload)
    assert result.status == ImportStatus.COMPLETED_WITH_ERRORS
    assert result.counters.failed == 1
    # The good record persisted; the failed record's menu item was rolled back.
    assert _item(db_session, "item-good-nutri") is not None
    assert _item(db_session, "item-bad-nutri") is None
    # The run and its structured error survive the per-record rollback.
    run = db_session.get(DataImport, result.import_id)
    assert run is not None and run.status == ImportStatus.COMPLETED_WITH_ERRORS
    persist_errors = db_session.scalars(
        select(DataImportError).where(DataImportError.code == "persist_failed")
    ).all()
    assert len(persist_errors) == 1


# --- Hierarchy & offering idempotency ------------------------------------


def _hierarchy_payload() -> dict:
    return {
        "institution": fx.INSTITUTION,
        "venues": [
            {
                "source_system": "fixture",
                "external_id": "bolton",
                "name": "Bolton",
                "slug": "bolton",
            }
        ],
        "stations": [
            {
                "source_system": "fixture",
                "external_id": "grill",
                "name": "Grill",
                "slug": "grill",
                "venue_external_id": "bolton",
            }
        ],
        "menu_items": [
            {
                "source_system": "fixture",
                "external_id": "item-offered",
                "name": "Offered Item",
                "station_external_id": "grill",
                "service_date": "2026-07-18",
                "meal_period": "lunch",
                "provided_nutrition": {
                    "serving_size": "1", "serving_unit": "each",
                    "nutrients": {"calories": "150"},
                },
            }
        ],
    }


def test_hierarchy_and_offerings_are_idempotent(db_session: Session) -> None:
    fx.run(db_session, _hierarchy_payload())
    fx.run(db_session, _hierarchy_payload())
    assert _count(db_session, Venue) == 1
    assert _count(db_session, Station) == 1
    assert _count(db_session, MenuOffering) == 1
