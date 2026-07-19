"""Contract validation for the recommendation engine (no database)."""

from __future__ import annotations

from decimal import Decimal

import pytest
import recommendation_fixtures as fx
from pydantic import ValidationError

from app.imports.contracts import NutrientValues
from app.recommendations.contracts import (
    AllergenInfo,
    DietaryTagInfo,
    RecommendationItem,
    UserPreferences,
)
from app.recommendations.exceptions import DuplicateItemIdError
from app.recommendations.service import recommend


def test_valid_item_input() -> None:
    item = fx.make_item()
    assert item.item_id == "item-1"
    assert item.nutrition is not None
    assert item.nutrition.nutrients.calories == Decimal("450")
    assert item.normalized_name == "grilled chicken"


def test_missing_nutrition_is_none_not_zero() -> None:
    item = fx.make_item(nutrition=None)
    assert item.nutrition is None

    partial = fx.make_nutrition(calories=None, protein_g=None)
    assert partial.nutrients.calories is None
    assert partial.nutrients.protein_g is None


def test_negative_nutrient_rejected() -> None:
    with pytest.raises(ValidationError):
        fx.make_nutrition(calories="-1")
    with pytest.raises(ValidationError):
        fx.make_nutrition(sodium_mg="-0.01")


@pytest.mark.parametrize("bad", ["NaN", "Infinity", "-Infinity"])
def test_nan_and_infinity_rejected(bad: str) -> None:
    with pytest.raises(ValidationError):
        fx.make_nutrition(calories=bad)
    with pytest.raises(ValidationError):
        fx.prefs(calorie_target=Decimal(bad))


def test_invalid_target_ranges_rejected() -> None:
    with pytest.raises(ValidationError):
        fx.prefs(calorie_min=Decimal("900"), calorie_max=Decimal("600"))
    # An equal min/max range is a valid (degenerate) range.
    equal = fx.prefs(calorie_min=Decimal("600"), calorie_max=Decimal("600"))
    assert equal.calorie_min == equal.calorie_max
    with pytest.raises(ValidationError):
        fx.prefs(calorie_target=Decimal("0"))
    with pytest.raises(ValidationError):
        fx.prefs(protein_target_g=Decimal("-5"))


def test_invalid_result_limits_rejected() -> None:
    with pytest.raises(ValidationError):
        fx.prefs(max_results=0)
    with pytest.raises(ValidationError):
        fx.prefs(max_results=51)
    assert fx.prefs(max_results=1).max_results == 1
    assert fx.prefs(max_results=50).max_results == 50


def test_duplicate_item_ids_rejected() -> None:
    items = [fx.make_item("dup", "A"), fx.make_item("dup", "B")]
    with pytest.raises(DuplicateItemIdError):
        recommend(items, fx.prefs())


def test_contracts_are_immutable() -> None:
    item = fx.make_item()
    with pytest.raises(ValidationError):
        item.name = "Changed"  # type: ignore[misc]
    preferences = fx.prefs()
    with pytest.raises(ValidationError):
        preferences.max_results = 5  # type: ignore[misc]


def test_unknown_fields_forbidden() -> None:
    with pytest.raises(ValidationError):
        RecommendationItem(item_id="x", name="X", surprise=True)  # type: ignore[call-arg]
    with pytest.raises(ValidationError):
        UserPreferences(surprise=True)  # type: ignore[call-arg]


def test_required_and_excluded_tag_overlap_rejected() -> None:
    with pytest.raises(ValidationError):
        fx.prefs(required_dietary_tags=("Vegan",), excluded_dietary_tags=("vegan",))


def test_preference_names_are_normalized_deduplicated_and_sorted() -> None:
    preferences = fx.prefs(
        excluded_allergens=("  Peanut ", "peanut", "MILK"),
        disliked_item_names=("Grilled  CHICKEN",),
        disliked_item_ids=("b", "a", "b"),
    )
    assert preferences.excluded_allergens == ("milk", "peanut")
    assert preferences.disliked_item_names == ("grilled chicken",)
    assert preferences.disliked_item_ids == ("a", "b")


def test_allergen_and_tag_validation() -> None:
    assert fx.allergen(" Tree  Nut ").name == "tree nut"
    assert fx.tag("Vegan").name == "vegan"
    with pytest.raises(ValidationError):
        AllergenInfo(name="   ")
    with pytest.raises(ValidationError):
        DietaryTagInfo(name="vegan", confidence=Decimal("1.5"))
    with pytest.raises(ValidationError):
        DietaryTagInfo(name="vegan", confidence=Decimal("-0.1"))


def test_blank_item_identity_rejected() -> None:
    with pytest.raises(ValidationError):
        RecommendationItem(item_id="", name="X")
    with pytest.raises(ValidationError):
        RecommendationItem(item_id="x", name="")


def test_nutrient_values_all_optional_default_none() -> None:
    values = NutrientValues()
    assert values.calories is None
    assert values.protein_g is None
