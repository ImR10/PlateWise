"""Service orchestration, plate assembly, logging, and app-level smoke tests."""

from __future__ import annotations

import logging
from decimal import Decimal

import pytest
import recommendation_fixtures as fx

from app.recommendations.enums import ResultWarning, SafetyMode
from app.recommendations.scoring import SCORING_POLICY_VERSION
from app.recommendations.service import recommend


def test_summary_and_policy_version() -> None:
    items = [
        fx.make_item("a", "Apple"),
        fx.make_item("b", "Bread", nutrition=None),
    ]
    result = recommend(
        items,
        fx.prefs(
            calorie_target=Decimal("1500"),
            protein_target_g=Decimal("90"),
            excluded_allergens=("peanut", "milk"),
            required_dietary_tags=("vegetarian",),
            disliked_item_ids=("zzz",),
        ),
    )
    summary = result.summary
    assert summary.total_items == 2
    assert summary.eligible_count + summary.excluded_count == 2
    assert summary.returned_count == result.result_count
    assert summary.has_calorie_target and summary.has_protein_target
    assert not summary.has_calorie_range
    assert summary.excluded_allergen_count == 2
    assert summary.required_dietary_tag_count == 1
    assert summary.disliked_item_count == 1
    assert result.scoring_policy_version == SCORING_POLICY_VERSION


def test_unknown_safety_exclusions_produce_result_warning() -> None:
    # Strict mode + excluded allergen + incomplete allergen data.
    items = [fx.make_item("a", "Apple", allergen_data_complete=False)]
    result = recommend(items, fx.prefs(excluded_allergens=("peanut",)))
    assert ResultWarning.ITEMS_EXCLUDED_UNKNOWN_SAFETY_DATA in result.warnings
    assert ResultWarning.NO_ELIGIBLE_ITEMS in result.warnings


def test_completion_log_event_is_structured_and_safe(
    caplog: pytest.LogCaptureFixture,
) -> None:
    items = [fx.make_item("a", "Apple Pie")]
    with caplog.at_level(logging.INFO, logger="app.recommendations.service"):
        recommend(items, fx.prefs(excluded_allergens=("peanut",), safety_mode="permissive"))
    records = [
        r for r in caplog.records if r.getMessage() == "recommendation_run_completed"
    ]
    assert len(records) == 1
    record = records[0]
    assert record.goal == "balanced"
    assert record.safety_mode == "permissive"
    assert record.input_item_count == 1
    assert record.eligible_count == 1
    assert record.excluded_count == 0
    assert record.scoring_policy_version == SCORING_POLICY_VERSION
    assert record.duration_ms >= 0
    # No payload details: item names and preference values are never logged.
    everything = str(record.__dict__)
    assert "Apple Pie" not in everything
    assert "peanut" not in everything


# --- Plate assembly --------------------------------------------------------


def test_plate_assembly_is_opt_in() -> None:
    result = recommend([fx.make_item()], fx.prefs())
    assert result.plate is None
    assert ResultWarning.PLATE_NOT_ASSEMBLED not in result.warnings


def test_plate_respects_calorie_budget_and_is_deterministic() -> None:
    items = [
        fx.make_item("a", "Apple", nutrition=fx.make_nutrition(calories="300")),
        fx.make_item("b", "Bread", nutrition=fx.make_nutrition(calories="400")),
        fx.make_item("c", "Cheese", nutrition=fx.make_nutrition(calories="900")),
        fx.make_item("d", "Dates", nutrition=fx.make_nutrition(calories="250")),
    ]
    preferences = fx.prefs(assemble_plate=True, calorie_target=Decimal("1000"))
    result = recommend(items, preferences)
    plate = result.plate
    assert plate is not None
    assert len(plate.item_ids) == len(set(plate.item_ids))  # no duplicates
    total = sum(
        (
            item.nutrition.nutrients.calories
            for item in items
            if item.item_id in plate.item_ids and item.nutrition is not None
        ),
        Decimal("0"),
    )
    assert total <= Decimal("1000") * Decimal("1.10")
    assert plate.totals.calories == total
    # Deterministic: same input, same plate.
    assert recommend(items, preferences).plate == plate


def test_plate_without_calorie_target_takes_top_ranked_with_warning() -> None:
    items = [fx.make_item(f"i{n}", f"Item {n}") for n in range(5)]
    result = recommend(items, fx.prefs(assemble_plate=True))
    plate = result.plate
    assert plate is not None
    assert len(plate.item_ids) == 3
    assert ResultWarning.PLATE_NO_CALORIE_TARGET in plate.warnings


def test_plate_totals_never_zero_fill_missing_nutrients() -> None:
    items = [
        fx.make_item("a", "Apple", nutrition=fx.make_nutrition(calories="300")),
        fx.make_item(
            "b",
            "Bread",
            nutrition=fx.make_nutrition(calories="400", fiber_g=None),
        ),
    ]
    result = recommend(
        items, fx.prefs(assemble_plate=True, calorie_target=Decimal("700"))
    )
    plate = result.plate
    assert plate is not None
    assert set(plate.item_ids) == {"a", "b"}
    assert plate.totals.calories == Decimal("700")
    assert plate.totals.fiber_g is None  # unknown stays unknown, never zero
    assert ResultWarning.PLATE_NUTRIENT_TOTALS_INCOMPLETE in plate.warnings


def test_plate_below_protein_target_warns() -> None:
    items = [fx.make_item("a", "Apple", nutrition=fx.make_nutrition(protein_g="10"))]
    result = recommend(
        items,
        fx.prefs(
            assemble_plate=True,
            calorie_target=Decimal("500"),
            protein_target_g=Decimal("60"),
        ),
    )
    plate = result.plate
    assert plate is not None
    assert ResultWarning.PLATE_BELOW_PROTEIN_TARGET in plate.warnings


def test_plate_not_assembled_when_no_item_fits_budget() -> None:
    # Permissive mode keeps calorie-less items eligible, but they cannot be
    # combined against a calorie budget.
    items = [
        fx.make_item(
            "a", "Apple", nutrition=fx.make_nutrition(calories=None, protein_g="5")
        )
    ]
    result = recommend(
        items,
        fx.prefs(
            assemble_plate=True,
            calorie_target=Decimal("600"),
            safety_mode=SafetyMode.PERMISSIVE,
        ),
    )
    assert result.plate is None
    assert ResultWarning.PLATE_NOT_ASSEMBLED in result.warnings


# --- Application-level smoke (engine must not disturb the app) -------------


def test_application_import_and_openapi_generation() -> None:
    from sqlalchemy.orm import configure_mappers

    from app.main import app

    configure_mappers()
    schema = app.openapi()
    assert schema["info"]["title"] == "PlateWise API"
