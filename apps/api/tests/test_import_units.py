"""Unit conversion, parsing, and portion-to-gram resolution tests."""

from __future__ import annotations

from decimal import Decimal

import import_fixtures as fx
import pytest

from app.db.enums import IngredientMatchMethod, IngredientResolutionStatus, RawOrCooked
from app.imports.contracts import ImportedRecipeIngredient
from app.imports.recipes.parser import parse_ingredient
from app.imports.recipes.resolver import resolve_ingredient
from app.imports.recipes.units import (
    is_mass_unit,
    is_vague,
    mass_to_grams,
    normalize_unit,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("oz", "oz"), ("Ounces", "oz"), ("g", "g"), ("grams", "g"), ("TBSP", "tbsp"), ("cups", "cup")],
)
def test_normalize_unit(raw: str, expected: str) -> None:
    assert normalize_unit(raw) == expected


def test_normalize_unit_unknown() -> None:
    assert normalize_unit("splash") is None
    assert normalize_unit(None) is None


def test_mass_to_grams_is_exact() -> None:
    # 6 oz -> 6 * 28.349523125 = 170.09713875 (exact, unrounded).
    assert mass_to_grams(Decimal("6"), "oz") == Decimal("170.09713875")
    assert mass_to_grams(Decimal("1"), "kg") == Decimal("1000")
    assert is_mass_unit("oz") and not is_mass_unit("cup")


def test_mass_to_grams_rejects_non_mass_unit() -> None:
    assert mass_to_grams(Decimal("1"), "cup") is None


def test_is_vague() -> None:
    assert is_vague("salt to taste")
    assert is_vague("oil for frying")
    assert not is_vague("6 oz chicken")


def test_parse_free_text_quantity_and_unit() -> None:
    parsed = parse_ingredient(
        ImportedRecipeIngredient(line_no=1, original_text="2 cups tomatoes, diced")
    )
    assert parsed.quantity == Decimal("2")
    assert parsed.unit == "cup"
    assert parsed.name == "tomatoes"
    assert parsed.preparation == "diced"


def test_parse_mixed_fraction() -> None:
    parsed = parse_ingredient(
        ImportedRecipeIngredient(line_no=1, original_text="1 1/2 oz cooked chicken")
    )
    assert parsed.quantity == Decimal("1.5")
    assert parsed.unit == "oz"
    assert parsed.raw_or_cooked == RawOrCooked.COOKED


def test_resolver_uses_provider_portion_weight() -> None:
    provider = fx.build_provider()
    parsed = parse_ingredient(
        ImportedRecipeIngredient(
            line_no=1,
            original_text="1 tbsp olive oil",
            quantity=Decimal("1"),
            unit="tbsp",
            name="olive oil",
            external_food_id="oil",
        )
    )
    resolved = resolve_ingredient(parsed, provider)
    assert resolved.status == IngredientResolutionStatus.RESOLVED
    assert resolved.grams == Decimal("13.5")  # exactly the provider portion weight
    assert resolved.match_method == IngredientMatchMethod.SOURCE_EXTERNAL_ID


def test_resolver_vague_quantity_is_unsupported() -> None:
    provider = fx.build_provider()
    parsed = parse_ingredient(
        ImportedRecipeIngredient(line_no=1, original_text="salt to taste", name="salt")
    )
    resolved = resolve_ingredient(parsed, provider)
    assert resolved.status == IngredientResolutionStatus.UNSUPPORTED_QUANTITY
    assert resolved.grams is None  # never guessed


def test_resolver_missing_match_is_flagged() -> None:
    provider = fx.build_provider()
    parsed = parse_ingredient(
        ImportedRecipeIngredient(
            line_no=1, original_text="1 cup dragonfruit", quantity=Decimal("1"),
            unit="cup", name="dragonfruit",
        )
    )
    resolved = resolve_ingredient(parsed, provider)
    assert resolved.status == IngredientResolutionStatus.NUTRITION_MATCH_MISSING
    assert resolved.grams is None


def test_resolver_excludes_non_nutritive() -> None:
    provider = fx.build_provider()
    parsed = parse_ingredient(
        ImportedRecipeIngredient(
            line_no=1, original_text="2 cups water", quantity=Decimal("2"), unit="cup", name="water"
        )
    )
    resolved = resolve_ingredient(parsed, provider)
    assert resolved.status == IngredientResolutionStatus.EXCLUDED_NON_NUTRITIVE
    assert not resolved.contributes_nutrition
