"""Development-seed tests: payload validity, full persistence, idempotency."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from platewise_db.enums import ImportStatus, NutritionProvenance, ProvenanceSourceType
from platewise_db.models import (
    Allergen,
    DataImport,
    DietaryTag,
    Institution,
    MenuItem,
    MenuItemAllergen,
    MenuItemDietaryTag,
    MenuOffering,
    NutritionFacts,
    Station,
    Venue,
)
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from platewise_api.dev import seed as seed_module
from platewise_api.dev.seed import run_seed
from platewise_api.dev.seed_data import SOURCE_SYSTEM, build_payload, build_provider
from platewise_api.imports import FixtureDiningSource, ImportCounters, ImportResult
from platewise_api.imports.sources.base import MenuItemParseOk

SERVICE_DATE = date(2026, 7, 20)


def _count(session: Session, model) -> int:
    return int(session.scalar(select(func.count()).select_from(model)) or 0)


# --- Payload validity (no database required) ------------------------------


def test_seed_payload_parses_with_no_errors() -> None:
    fetched = FixtureDiningSource(build_payload(SERVICE_DATE)).fetch()

    assert fetched.warnings == ()
    assert len(fetched.venues) == 2
    assert len(fetched.stations) == 5
    assert len(fetched.menu_items) == 12
    assert all(isinstance(result, MenuItemParseOk) for result in fetched.menu_items)


def test_seed_recipe_ingredients_all_resolve() -> None:
    provider = build_provider()
    fetched = FixtureDiningSource(build_payload(SERVICE_DATE)).fetch()

    for result in fetched.menu_items:
        assert isinstance(result, MenuItemParseOk)
        if result.item.recipe is None:
            continue
        for ingredient in result.item.recipe.ingredients:
            assert ingredient.external_food_id is not None
            assert provider.get_food(ingredient.external_food_id) is not None


# --- Full pipeline persistence (database-backed) --------------------------


def test_seed_populates_catalog_cleanly(db_session: Session) -> None:
    summary = run_seed(db_session, SERVICE_DATE)
    result = summary.import_result

    assert result.status is ImportStatus.COMPLETED
    assert result.error_count == 0
    assert result.warning_count == 0
    assert result.counters.created == 12
    assert result.counters.failed == 0
    assert result.counters.nutrition_provided == 10
    assert result.counters.nutrition_calculated == 2
    assert result.counters.ingredients_unresolved == 0

    assert _count(db_session, Institution) == 1
    assert _count(db_session, Venue) == 2
    assert _count(db_session, Station) == 5
    assert _count(db_session, MenuItem) == 12
    assert _count(db_session, MenuOffering) == 12
    assert _count(db_session, NutritionFacts) == 12

    assert summary.allergen_links_created == 9
    assert summary.dietary_tag_links_created == 16
    assert _count(db_session, Allergen) == 4  # Eggs, Milk, Wheat, Soy
    assert _count(db_session, DietaryTag) == 3  # Vegan, Vegetarian, Gluten-Free


def test_seed_metadata_uses_imported_provenance(db_session: Session) -> None:
    run_seed(db_session, SERVICE_DATE)

    assert set(db_session.scalars(select(MenuItemAllergen.source_type))) == {
        ProvenanceSourceType.IMPORTED
    }
    assert set(db_session.scalars(select(MenuItemDietaryTag.source_type))) == {
        ProvenanceSourceType.IMPORTED
    }


def test_seed_nutrition_is_displayable(db_session: Session) -> None:
    run_seed(db_session, SERVICE_DATE)

    provided = db_session.scalar(
        select(MenuItem).where(MenuItem.external_id == "seed-item-grilled-chicken")
    )
    assert provided is not None
    facts = provided.display_nutrition()
    assert facts is not None
    assert facts.provenance == NutritionProvenance.SOURCE_PROVIDED
    assert facts.calories == Decimal("240.00")

    calculated = db_session.scalar(
        select(MenuItem).where(MenuItem.external_id == "seed-item-chicken-rice-bowl")
    )
    assert calculated is not None
    calc_facts = calculated.display_nutrition()
    assert calc_facts is not None
    assert calc_facts.provenance == NutritionProvenance.RECIPE_CALCULATED
    assert calc_facts.is_complete
    assert calc_facts.calories is not None


def test_seed_is_idempotent(db_session: Session) -> None:
    run_seed(db_session, SERVICE_DATE)
    counts_after_first = {
        model: _count(db_session, model)
        for model in (
            Institution,
            Venue,
            Station,
            MenuItem,
            MenuOffering,
            NutritionFacts,
            Allergen,
            DietaryTag,
            MenuItemAllergen,
            MenuItemDietaryTag,
        )
    }

    second = run_seed(db_session, SERVICE_DATE)

    assert second.import_result.status is ImportStatus.COMPLETED
    assert second.import_result.counters.created == 0
    assert second.import_result.counters.updated == 0
    assert second.import_result.counters.unchanged == 12
    assert second.allergen_links_created == 0
    assert second.dietary_tag_links_created == 0
    for model, count_before in counts_after_first.items():
        assert _count(db_session, model) == count_before, model.__name__


def test_seed_creates_distinct_offerings_for_each_date(db_session: Session) -> None:
    second_date = date(2026, 7, 21)

    run_seed(db_session, SERVICE_DATE)
    run_seed(db_session, second_date)

    assert _count(db_session, MenuItem) == 12
    assert _count(db_session, MenuOffering) == 24
    for service_date in (SERVICE_DATE, second_date):
        count = db_session.scalar(
            select(func.count())
            .select_from(MenuOffering)
            .where(MenuOffering.service_date == service_date)
        )
        assert count == 12

    run_seed(db_session, second_date)

    assert _count(db_session, MenuItem) == 12
    assert _count(db_session, MenuOffering) == 24


def test_unsuccessful_seed_rolls_back_catalog_and_skips_metadata(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_build_payload = seed_module.build_payload

    def build_malformed_payload(service_date: date):
        payload = original_build_payload(service_date)
        payload["menu_items"].append(
            {
                "source_system": SOURCE_SYSTEM,
                "external_id": "seed-invalid-item",
                # Missing the required name makes this final record fail after
                # earlier records have exercised persistence.
            }
        )
        return payload

    monkeypatch.setattr(seed_module, "build_payload", build_malformed_payload)

    summary = run_seed(db_session, SERVICE_DATE)
    db_session.commit()

    assert summary.import_result.status is ImportStatus.FAILED
    assert summary.allergen_links_created == 0
    assert summary.dietary_tag_links_created == 0
    assert _count(db_session, MenuItem) == 0
    assert _count(db_session, MenuOffering) == 0
    assert _count(db_session, NutritionFacts) == 0
    assert _count(db_session, Allergen) == 0
    assert _count(db_session, DietaryTag) == 0
    assert _count(db_session, MenuItemAllergen) == 0
    assert _count(db_session, MenuItemDietaryTag) == 0
    failed_run = db_session.scalar(select(DataImport))
    assert failed_run is not None
    assert failed_run.status is ImportStatus.FAILED


def test_completed_with_errors_skips_metadata_supplement(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    incomplete_result = ImportResult(
        import_id=uuid4(),
        status=ImportStatus.COMPLETED_WITH_ERRORS,
        counters=ImportCounters(failed=1),
        error_count=1,
    )

    def incomplete_import(*args, **kwargs):
        assert kwargs["tolerant"] is False
        return incomplete_result

    def unexpected_supplement(_session: Session):
        raise AssertionError("metadata supplement must not run")

    monkeypatch.setattr(seed_module, "run_import", incomplete_import)
    monkeypatch.setattr(seed_module, "_apply_catalog_metadata", unexpected_supplement)

    summary = run_seed(db_session, SERVICE_DATE)

    assert summary.import_result is incomplete_result
    assert summary.allergen_links_created == 0
    assert summary.dietary_tag_links_created == 0


def test_seed_records_are_scoped_to_the_seed_source(db_session: Session) -> None:
    run_seed(db_session, SERVICE_DATE)

    sources = set(db_session.scalars(select(MenuItem.source_system)))
    assert sources == {SOURCE_SYSTEM}
