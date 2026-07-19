"""Focused import-boundary, identity, provider, and performance hardening tests."""

from __future__ import annotations

from decimal import Decimal

import import_fixtures as fx
import pytest
from pydantic import ValidationError

from app.imports.contracts import (
    ImportedRecipeIngredient,
    NutrientValues,
)
from app.imports.exceptions import SourceError
from app.imports.nutrition.provider import (
    CachingIngredientNutritionProvider,
    FakeIngredientNutritionProvider,
    ProviderFoodData,
    ProviderPortion,
)
from app.imports.repositories import recipe_content_hash
from app.imports.sources.fixture import FixtureDiningSource


@pytest.mark.parametrize("value", ["-0.01", "NaN", "Infinity", "999999999.00"])
def test_nutrients_reject_negative_non_finite_and_overflow(value: str) -> None:
    with pytest.raises(ValidationError):
        NutrientValues(calories=value)


def test_negative_ingredient_quantity_is_rejected() -> None:
    with pytest.raises(ValidationError):
        ImportedRecipeIngredient(line_no=1, original_text="-1 oz chicken", quantity="-1")


@pytest.mark.parametrize("weight", ["0", "-1", "NaN", "Infinity"])
def test_provider_portion_requires_positive_finite_weight(weight: str) -> None:
    with pytest.raises(ValidationError):
        ProviderPortion(description="cup", gram_weight=weight)


def test_provider_food_rejects_duplicate_normalized_portions() -> None:
    with pytest.raises(ValidationError, match="duplicate normalized"):
        ProviderFoodData(
            provider="fake",
            provider_food_id="rice",
            name="rice",
            portions=(
                ProviderPortion(description="cup", gram_weight="150"),
                ProviderPortion(description=" CUP ", gram_weight="151"),
            ),
        )


def test_fixture_rejects_malformed_top_level_collection() -> None:
    payload = {"institution": fx.INSTITUTION, "menu_items": "not-a-list"}
    with pytest.raises(SourceError, match="must be a list"):
        FixtureDiningSource(payload).fetch()


def test_fixture_rejects_excessive_json_depth() -> None:
    nested: dict[str, object] = {}
    cursor = nested
    for _ in range(35):
        child: dict[str, object] = {}
        cursor["child"] = child
        cursor = child
    payload = {"institution": fx.INSTITUTION, "metadata": nested}
    with pytest.raises(SourceError, match="depth limit"):
        FixtureDiningSource(payload).fetch()


def test_fixture_isolates_duplicate_item_identity() -> None:
    payload = fx.fixture_1_source_nutrition()
    payload["menu_items"].append(dict(payload["menu_items"][0]))
    fetched = FixtureDiningSource(payload).fetch()
    assert len(fetched.menu_items) == 2
    assert type(fetched.menu_items[1]).__name__ == "MenuItemParseError"


def test_fixture_rejects_conflicting_hierarchy_source_system() -> None:
    payload = {
        "institution": fx.INSTITUTION,
        "venues": [
            {"source_system": "spoofed", "name": "Other", "slug": "other"}
        ],
    }
    with pytest.raises(SourceError, match="conflicting source_system"):
        FixtureDiningSource(payload).fetch()


def test_recipe_source_text_participates_in_version_hash() -> None:
    payload = fx.fixture_2_resolvable_recipe()
    recipe = payload["menu_items"][0]["recipe"]
    from app.imports.contracts import ImportedRecipe

    first = ImportedRecipe.model_validate({**recipe, "source_text": "first body"})
    second = ImportedRecipe.model_validate({**recipe, "source_text": "second body"})
    assert recipe_content_hash(first) != recipe_content_hash(second)


class _CountingProvider:
    provider_name = "fake"

    def __init__(self, food: ProviderFoodData) -> None:
        self.food = food
        self.get_calls = 0
        self.search_calls = 0

    def get_food(self, external_food_id: str) -> ProviderFoodData | None:
        self.get_calls += 1
        return self.food if external_food_id == self.food.provider_food_id else None

    def search_food(self, query: str) -> ProviderFoodData | None:
        self.search_calls += 1
        return self.food if query == self.food.name else None


def test_run_cache_reduces_repeated_provider_calls_from_two_to_one() -> None:
    food = ProviderFoodData(
        provider="fake",
        provider_food_id="chicken",
        name="chicken breast",
    )
    underlying = _CountingProvider(food)
    cached = CachingIngredientNutritionProvider(underlying)
    assert cached.get_food("chicken") is food
    assert cached.get_food("chicken") is food
    assert cached.search_food("chicken breast") is food
    assert cached.search_food("  CHICKEN   BREAST ") is food
    assert underlying.get_calls == 1
    assert underlying.search_calls == 1


def test_fake_provider_rejects_ambiguous_aliases() -> None:
    foods = [
        ProviderFoodData(
            provider="fake", provider_food_id="one", name="Food One", search_aliases=("same",)
        ),
        ProviderFoodData(
            provider="fake", provider_food_id="two", name="Food Two", search_aliases=("same",)
        ),
    ]
    with pytest.raises(ValueError, match="ambiguous"):
        FakeIngredientNutritionProvider(foods)


def test_zero_servings_remains_representable_for_failed_calculation() -> None:
    payload = fx.fixture_2_resolvable_recipe()
    payload["menu_items"][0]["recipe"]["servings"] = "0"
    fetched = FixtureDiningSource(payload).fetch()
    item = fetched.menu_items[0].item  # type: ignore[union-attr]
    assert item.recipe is not None and item.recipe.servings == Decimal("0")
