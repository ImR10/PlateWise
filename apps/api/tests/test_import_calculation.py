"""Recipe nutrition calculation tests (Decimal, per-serving, completeness)."""

from __future__ import annotations

from decimal import Decimal

import import_fixtures as fx

from app.db.enums import CalculationStatus
from app.imports.contracts import ImportedRecipeIngredient
from app.imports.recipes.calculator import calculate_recipe_nutrition
from app.imports.recipes.parser import parse_ingredient
from app.imports.recipes.resolver import resolve_ingredient


def _resolve(lines: list[ImportedRecipeIngredient]):
    provider = fx.build_provider()
    return [resolve_ingredient(parse_ingredient(line), provider) for line in lines]


CHICKEN_6OZ = ImportedRecipeIngredient(
    line_no=1, original_text="6 oz chicken breast", quantity=Decimal("6"), unit="oz",
    name="chicken breast", external_food_id="chicken",
)
OIL_1TBSP = ImportedRecipeIngredient(
    line_no=2, original_text="1 tbsp olive oil", quantity=Decimal("1"), unit="tbsp",
    name="olive oil", external_food_id="oil",
)


def test_calculation_is_exact_and_complete() -> None:
    resolved = _resolve([CHICKEN_6OZ, OIL_1TBSP])
    calc = calculate_recipe_nutrition(Decimal("2"), resolved)
    assert calc.status == CalculationStatus.COMPLETE
    assert calc.is_complete
    # chicken 6oz=170.09713875g @165/100 + oil 13.5g @884/100 = 400.00 cal total; /2 = 200.00
    assert calc.per_serving["calories"] == Decimal("200.00")
    assert calc.per_serving["protein_g"] == Decimal("26.37")


def test_calculation_is_deterministic() -> None:
    first = calculate_recipe_nutrition(Decimal("2"), _resolve([CHICKEN_6OZ, OIL_1TBSP]))
    second = calculate_recipe_nutrition(Decimal("2"), _resolve([CHICKEN_6OZ, OIL_1TBSP]))
    assert first.per_serving == second.per_serving


def test_unresolved_ingredient_makes_calculation_partial() -> None:
    dragonfruit = ImportedRecipeIngredient(
        line_no=2, original_text="1 cup dragonfruit", quantity=Decimal("1"), unit="cup",
        name="dragonfruit",
    )
    calc = calculate_recipe_nutrition(Decimal("2"), _resolve([CHICKEN_6OZ, dragonfruit]))
    assert calc.status == CalculationStatus.PARTIAL
    assert not calc.is_complete
    assert calc.unresolved_count == 1
    # The resolved chicken still yields a retained subtotal (not zeroed away).
    assert calc.per_serving["calories"] is not None


def test_missing_servings_makes_calculation_failed() -> None:
    calc = calculate_recipe_nutrition(None, _resolve([CHICKEN_6OZ, OIL_1TBSP]))
    assert calc.status == CalculationStatus.FAILED
    assert not calc.is_complete
    assert all(value is None for value in calc.per_serving.values())


def test_missing_nutrient_is_never_zeroed() -> None:
    """A provider food missing a nutrient makes that nutrient unknown, not zero."""
    from app.imports.contracts import NutrientValues
    from app.imports.nutrition.provider import (
        FakeIngredientNutritionProvider,
        ProviderFoodData,
    )

    provider = FakeIngredientNutritionProvider(
        [
            ProviderFoodData(
                provider="fake",
                provider_food_id="partialfood",
                name="partial food",
                # cholesterol_mg intentionally omitted (None).
                nutrients=NutrientValues(calories=Decimal("100"), protein_g=Decimal("10")),
            )
        ]
    )
    line = ImportedRecipeIngredient(
        line_no=1, original_text="100 g partial food", quantity=Decimal("100"), unit="g",
        name="partial food", external_food_id="partialfood",
    )
    resolved = [resolve_ingredient(parse_ingredient(line), provider)]
    calc = calculate_recipe_nutrition(Decimal("1"), resolved)
    assert calc.per_serving["calories"] == Decimal("100.00")
    assert calc.per_serving["cholesterol_mg"] is None  # unknown, not 0
    assert not calc.is_complete  # missing nutrient -> not authoritative
