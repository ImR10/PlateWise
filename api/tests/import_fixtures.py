"""Deterministic fixtures for import tests.

Provides a fake ingredient-nutrition provider with a small known food catalog
and the 10 source payloads required by the milestone plan. Everything is
deterministic: no randomness, no network, exact ``Decimal`` values.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from platewise_api.imports import (
    FakeIngredientNutritionProvider,
    FixtureDiningSource,
    ImportResult,
    ProviderFoodData,
    ProviderPortion,
    run_import,
)
from platewise_api.imports.contracts import NutrientValues


def _n(**kwargs: str) -> NutrientValues:
    return NutrientValues(**{k: Decimal(v) for k, v in kwargs.items()})


def build_provider() -> FakeIngredientNutritionProvider:
    """A fake provider with fully-specified per-100 g foods and portions."""
    return FakeIngredientNutritionProvider(
        [
            ProviderFoodData(
                provider="fake",
                provider_food_id="chicken",
                name="chicken breast",
                nutrients=_n(
                    calories="165",
                    protein_g="31",
                    carbohydrates_g="0",
                    fat_g="3.6",
                    saturated_fat_g="1.0",
                    fiber_g="0",
                    sugar_g="0",
                    sodium_mg="74",
                    cholesterol_mg="85",
                ),
            ),
            ProviderFoodData(
                provider="fake",
                provider_food_id="oil",
                name="olive oil",
                nutrients=_n(
                    calories="884",
                    protein_g="0",
                    carbohydrates_g="0",
                    fat_g="100",
                    saturated_fat_g="13.8",
                    fiber_g="0",
                    sugar_g="0",
                    sodium_mg="2",
                    cholesterol_mg="0",
                ),
                portions=(ProviderPortion(description="tbsp", gram_weight=Decimal("13.5")),),
            ),
            ProviderFoodData(
                provider="fake",
                provider_food_id="rice_cooked",
                name="cooked white rice",
                search_aliases=("white rice",),
                nutrients=_n(
                    calories="130",
                    protein_g="2.7",
                    carbohydrates_g="28",
                    fat_g="0.3",
                    saturated_fat_g="0.1",
                    fiber_g="0.4",
                    sugar_g="0.1",
                    sodium_mg="1",
                    cholesterol_mg="0",
                ),
                portions=(ProviderPortion(description="cup", gram_weight=Decimal("158")),),
            ),
            ProviderFoodData(
                provider="fake",
                provider_food_id="onion",
                name="onion",
                nutrients=_n(
                    calories="40",
                    protein_g="1.1",
                    carbohydrates_g="9.3",
                    fat_g="0.1",
                    saturated_fat_g="0",
                    fiber_g="1.7",
                    sugar_g="4.2",
                    sodium_mg="4",
                    cholesterol_mg="0",
                ),
                portions=(ProviderPortion(description="medium", gram_weight=Decimal("110")),),
            ),
        ]
    )


def run(
    session: Session,
    payload: dict[str, Any],
    provider: FakeIngredientNutritionProvider | None = None,
    *,
    tolerant: bool = True,
) -> ImportResult:
    """Run an import of ``payload`` and return the result."""
    provider = provider or build_provider()
    return run_import(session, FixtureDiningSource(payload), provider, tolerant=tolerant)


# --- The 10 required fixtures ---------------------------------------------

INSTITUTION = {"source_system": "fixture", "external_id": "uga", "name": "UGA", "slug": "uga"}


def fixture_1_source_nutrition() -> dict[str, Any]:
    """A valid item with source-provided nutrition."""
    return {
        "institution": INSTITUTION,
        "menu_items": [
            {
                "source_system": "fixture",
                "external_id": "item-chicken",
                "name": "Grilled Chicken Breast",
                "serving_size": "1",
                "serving_unit": "breast",
                "provided_nutrition": {
                    "serving_size": "1",
                    "serving_unit": "breast",
                    "nutrients": {
                        "calories": "240",
                        "protein_g": "36",
                        "carbohydrates_g": "2",
                        "fat_g": "9",
                        "sodium_mg": "420",
                    },
                    "source_reference": "dining-label-2026",
                },
            }
        ],
    }


def fixture_2_resolvable_recipe() -> dict[str, Any]:
    """A valid structured recipe with fully resolvable ingredients."""
    return {
        "institution": INSTITUTION,
        "menu_items": [
            {
                "source_system": "fixture",
                "external_id": "item-chicken-rice",
                "name": "Chicken and Rice",
                "recipe": {
                    "source_system": "fixture",
                    "external_id": "recipe-cr-1",
                    "servings": "2",
                    "yield_unit": "servings",
                    "ingredients": [
                        {
                            "line_no": 1,
                            "original_text": "6 oz chicken breast",
                            "quantity": "6",
                            "unit": "oz",
                            "name": "chicken breast",
                            "external_food_id": "chicken",
                        },
                        {
                            "line_no": 2,
                            "original_text": "1 tbsp olive oil",
                            "quantity": "1",
                            "unit": "tbsp",
                            "name": "olive oil",
                            "external_food_id": "oil",
                        },
                        {
                            "line_no": 3,
                            "original_text": "1 cup cooked white rice",
                            "quantity": "1",
                            "unit": "cup",
                            "name": "cooked white rice",
                            "external_food_id": "rice_cooked",
                        },
                    ],
                },
            }
        ],
    }


def fixture_3_vague_quantity() -> dict[str, Any]:
    """A recipe with a vague quantity ("salt to taste")."""
    return {
        "institution": INSTITUTION,
        "menu_items": [
            {
                "source_system": "fixture",
                "external_id": "item-vague",
                "name": "Seasoned Chicken",
                "recipe": {
                    "source_system": "fixture",
                    "external_id": "recipe-vague-1",
                    "servings": "2",
                    "ingredients": [
                        {
                            "line_no": 1,
                            "original_text": "6 oz chicken breast",
                            "quantity": "6",
                            "unit": "oz",
                            "name": "chicken breast",
                            "external_food_id": "chicken",
                        },
                        {
                            "line_no": 2,
                            "original_text": "salt to taste",
                            "name": "salt",
                        },
                    ],
                },
            }
        ],
    }


def fixture_4_unresolved_ingredient() -> dict[str, Any]:
    """A recipe with an ingredient no provider food matches."""
    return {
        "institution": INSTITUTION,
        "menu_items": [
            {
                "source_system": "fixture",
                "external_id": "item-unresolved",
                "name": "Exotic Bowl",
                "recipe": {
                    "source_system": "fixture",
                    "external_id": "recipe-unresolved-1",
                    "servings": "2",
                    "ingredients": [
                        {
                            "line_no": 1,
                            "original_text": "6 oz chicken breast",
                            "quantity": "6",
                            "unit": "oz",
                            "name": "chicken breast",
                            "external_food_id": "chicken",
                        },
                        {
                            "line_no": 2,
                            "original_text": "1 cup dragonfruit",
                            "quantity": "1",
                            "unit": "cup",
                            "name": "dragonfruit",
                        },
                    ],
                },
            }
        ],
    }


def fixture_5_missing_serving_basis() -> dict[str, Any]:
    """Provided nutrient values but no serving basis."""
    return {
        "institution": INSTITUTION,
        "menu_items": [
            {
                "source_system": "fixture",
                "external_id": "item-nobasis",
                "name": "Mystery Portion",
                "provided_nutrition": {
                    "nutrients": {"calories": "300", "protein_g": "20"},
                },
            }
        ],
    }


def fixture_6_missing_yield() -> dict[str, Any]:
    """A recipe with resolvable ingredients but no servings/yield."""
    return {
        "institution": INSTITUTION,
        "menu_items": [
            {
                "source_system": "fixture",
                "external_id": "item-noyield",
                "name": "Unportioned Recipe",
                "recipe": {
                    "source_system": "fixture",
                    "external_id": "recipe-noyield-1",
                    "ingredients": [
                        {
                            "line_no": 1,
                            "original_text": "6 oz chicken breast",
                            "quantity": "6",
                            "unit": "oz",
                            "name": "chicken breast",
                            "external_food_id": "chicken",
                        }
                    ],
                },
            }
        ],
    }


def fixture_7_malformed_record() -> dict[str, Any]:
    """One malformed menu-item record (missing required 'name') among valid ones."""
    return {
        "institution": INSTITUTION,
        "menu_items": [
            {
                "source_system": "fixture",
                "external_id": "item-ok",
                "name": "Good Item",
                "provided_nutrition": {
                    "serving_size": "1",
                    "serving_unit": "each",
                    "nutrients": {"calories": "100"},
                },
            },
            {
                "source_system": "fixture",
                "external_id": "item-bad",
                # 'name' is required -> this record is malformed.
                "provided_nutrition": {"nutrients": {"calories": "999"}},
            },
        ],
    }


def fixture_8_repeat() -> dict[str, Any]:
    """Reuse the resolvable-recipe fixture for repeated-import idempotency."""
    return fixture_2_resolvable_recipe()


def fixture_9_both_nutrition() -> dict[str, Any]:
    """A source item with both provided nutrition and a calculable recipe."""
    return {
        "institution": INSTITUTION,
        "menu_items": [
            {
                "source_system": "fixture",
                "external_id": "item-both",
                "name": "Chicken (both)",
                "serving_size": "1",
                "serving_unit": "serving",
                "provided_nutrition": {
                    "serving_size": "1",
                    "serving_unit": "serving",
                    "nutrients": {"calories": "205", "protein_g": "26"},
                    "source_reference": "label",
                },
                "recipe": {
                    "source_system": "fixture",
                    "external_id": "recipe-both-1",
                    "servings": "2",
                    "ingredients": [
                        {
                            "line_no": 1,
                            "original_text": "6 oz chicken breast",
                            "quantity": "6",
                            "unit": "oz",
                            "name": "chicken breast",
                            "external_food_id": "chicken",
                        },
                        {
                            "line_no": 2,
                            "original_text": "1 tbsp olive oil",
                            "quantity": "1",
                            "unit": "tbsp",
                            "name": "olive oil",
                            "external_food_id": "oil",
                        },
                    ],
                },
            }
        ],
    }


def fixture_10_empty() -> dict[str, Any]:
    """A suspiciously empty source response (valid institution, no items)."""
    return {"institution": INSTITUTION, "menu_items": []}
