"""Ingredient resolution: parsed line -> canonical provider food + grams.

Resolution is deterministic and honest about failure. A line is only
``RESOLVED`` when it has a matched provider food *and* a trustworthy gram
weight. Every other outcome is a typed status that preserves the line for review
and contributes **no** nutrition -- an unresolved ingredient is never treated as
zero.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.db.enums import IngredientMatchMethod, IngredientResolutionStatus
from app.imports.decimal_utils import to_decimal
from app.imports.normalizers import normalize_name
from app.imports.nutrition.provider import (
    IngredientNutritionProvider,
    ProviderFoodData,
    ProviderPortion,
)
from app.imports.recipes.parser import ParsedIngredient
from app.imports.recipes.units import is_mass_unit, mass_to_grams

# Non-nutritive ingredients contribute nothing and are excluded from totals
# without being treated as an error.
EXCLUDED_NON_NUTRITIVE: frozenset[str] = frozenset({"water"})

_CONFIDENCE_EXTERNAL_ID = Decimal("1.00")
_CONFIDENCE_SEARCH = Decimal("0.80")


@dataclass(frozen=True)
class ResolvedIngredient:
    """The outcome of resolving one parsed ingredient line."""

    parsed: ParsedIngredient
    status: IngredientResolutionStatus
    provider_food: ProviderFoodData | None = None
    grams: Decimal | None = None
    match_method: IngredientMatchMethod | None = None
    confidence: Decimal | None = None
    error_detail: str | None = None

    @property
    def contributes_nutrition(self) -> bool:
        return (
            self.status == IngredientResolutionStatus.RESOLVED
            and self.provider_food is not None
            and self.grams is not None
        )


def _find_portion(food: ProviderFoodData, unit_token: str | None) -> ProviderPortion | None:
    if unit_token is None:
        return None
    target = normalize_name(unit_token)
    for portion in food.portions:
        if normalize_name(portion.description) == target:
            return portion
    return None


def _resolve_food(
    parsed: ParsedIngredient, provider: IngredientNutritionProvider
) -> tuple[ProviderFoodData | None, IngredientMatchMethod]:
    if parsed.external_food_id:
        food = provider.get_food(parsed.external_food_id)
        if food is not None:
            return food, IngredientMatchMethod.SOURCE_EXTERNAL_ID
        return None, IngredientMatchMethod.UNMATCHED
    if parsed.name:
        food = provider.search_food(parsed.name)
        if food is not None:
            return food, IngredientMatchMethod.PROVIDER_SEARCH
    return None, IngredientMatchMethod.UNMATCHED


def resolve_ingredient(
    parsed: ParsedIngredient, provider: IngredientNutritionProvider
) -> ResolvedIngredient:
    """Resolve a parsed ingredient line against the nutrition provider."""
    # 1. Non-nutritive exclusions (water, ...): valid but contribute nothing.
    if parsed.normalized_name in EXCLUDED_NON_NUTRITIVE:
        return ResolvedIngredient(
            parsed=parsed,
            status=IngredientResolutionStatus.EXCLUDED_NON_NUTRITIVE,
            error_detail="excluded non-nutritive ingredient",
        )

    # 2. Vague or missing amounts are never guessed.
    if parsed.is_vague:
        return ResolvedIngredient(
            parsed=parsed,
            status=IngredientResolutionStatus.UNSUPPORTED_QUANTITY,
            error_detail="vague quantity (e.g. 'to taste')",
        )
    if parsed.quantity is None:
        return ResolvedIngredient(
            parsed=parsed,
            status=IngredientResolutionStatus.UNSUPPORTED_QUANTITY,
            error_detail="missing quantity",
        )

    # 3. Resolve the canonical food.
    food, match_method = _resolve_food(parsed, provider)
    if food is None:
        return ResolvedIngredient(
            parsed=parsed,
            status=IngredientResolutionStatus.NUTRITION_MATCH_MISSING,
            match_method=IngredientMatchMethod.UNMATCHED,
            error_detail="no provider food matched",
        )

    confidence = (
        _CONFIDENCE_EXTERNAL_ID
        if match_method == IngredientMatchMethod.SOURCE_EXTERNAL_ID
        else _CONFIDENCE_SEARCH
    )

    # 4. Convert the quantity to grams (mass factor or resolved provider portion).
    grams: Decimal | None = None
    if is_mass_unit(parsed.unit):
        grams = mass_to_grams(parsed.quantity, parsed.unit)  # type: ignore[arg-type]
    else:
        portion = _find_portion(food, parsed.unit) or _find_portion(food, parsed.raw_unit)
        if portion is not None:
            grams = to_decimal(parsed.quantity) * portion.gram_weight

    if grams is None:
        return ResolvedIngredient(
            parsed=parsed,
            status=IngredientResolutionStatus.UNSUPPORTED_QUANTITY,
            provider_food=food,
            match_method=match_method,
            confidence=confidence,
            error_detail=(
                f"no gram conversion for unit {parsed.raw_unit!r} "
                "(not a mass unit and no matching provider portion)"
            ),
        )

    return ResolvedIngredient(
        parsed=parsed,
        status=IngredientResolutionStatus.RESOLVED,
        provider_food=food,
        grams=grams,
        match_method=match_method,
        confidence=confidence,
    )
