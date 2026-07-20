"""Basic deterministic plate assembly (optional, opt-in).

Intentionally limited for the MVP: a single greedy pass over the ranked
eligible items — no combinatorial optimization, meal planning, or multi-day
logic. Hard constraints were already enforced by the filters, so every
candidate here is safe to combine.

Rules:

* at most :data:`MAX_PLATE_ITEMS` distinct items, no duplicates;
* with a calorie budget (target or range), only items with known calories are
  combined, the budget's upper bound is never exceeded, and selection stops
  once the lower bound is reached;
* without a calorie budget the plate is simply the top
  :data:`DEFAULT_PLATE_SIZE` ranked items, with an explicit warning;
* nutrient totals sum one serving of each selected item and are ``None`` when
  any selected item's value is unknown — never zero-filled.
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from platewise_db.constants import NUTRIENT_FIELDS
from platewise_db.decimal_utils import quantize_nutrient

from platewise_api.recommendations.contracts import (
    NutrientValues,
    PlateSuggestion,
    RecommendationItem,
    ScoredRecommendation,
    UserPreferences,
)
from platewise_api.recommendations.enums import ResultWarning

MAX_PLATE_ITEMS = 4
#: Plate size when the user set no calorie target or range.
DEFAULT_PLATE_SIZE = 3
#: Relative band applied around a bare calorie target (no explicit range).
CALORIE_TOLERANCE = Decimal("0.10")

_ONE = Decimal("1")


def _calorie_bounds(preferences: UserPreferences) -> tuple[Decimal | None, Decimal | None]:
    """The plate-level calorie budget: (lower bound, upper bound)."""
    if preferences.calorie_min is not None or preferences.calorie_max is not None:
        return preferences.calorie_min, preferences.calorie_max
    if preferences.calorie_target is not None:
        target = preferences.calorie_target
        return target * (_ONE - CALORIE_TOLERANCE), target * (_ONE + CALORIE_TOLERANCE)
    return None, None


def _totals(
    selected: Sequence[RecommendationItem],
) -> tuple[NutrientValues, bool]:
    """Sum one serving of each item; ``None`` where any value is unknown."""
    sums: dict[str, Decimal | None] = {}
    incomplete = False
    for field in NUTRIENT_FIELDS:
        values = [
            item.nutrition.nutrients if item.nutrition is not None else None for item in selected
        ]
        nutrient_values = [
            getattr(nutrients, field) if nutrients is not None else None for nutrients in values
        ]
        if any(value is None for value in nutrient_values):
            sums[field] = None
            incomplete = True
        else:
            total = sum(nutrient_values, Decimal("0"))
            sums[field] = quantize_nutrient(total)
    return NutrientValues(**sums), incomplete


def assemble_plate(
    ranked: Sequence[tuple[ScoredRecommendation, RecommendationItem]],
    preferences: UserPreferences,
) -> PlateSuggestion | None:
    """Greedily combine ranked eligible items into one deterministic plate."""
    if not ranked:
        return None

    low, high = _calorie_bounds(preferences)
    warnings: list[ResultWarning] = []
    selected: list[RecommendationItem] = []

    if low is None and high is None:
        selected = [item for _, item in ranked[:DEFAULT_PLATE_SIZE]]
        warnings.append(ResultWarning.PLATE_NO_CALORIE_TARGET)
        explanation = "Combines the top-ranked eligible items; no calorie target was set."
    else:
        total_calories = Decimal("0")
        for _, item in ranked:
            if len(selected) >= MAX_PLATE_ITEMS:
                break
            if low is not None and total_calories >= low:
                break
            nutrition = item.nutrition
            calories = nutrition.nutrients.calories if nutrition is not None else None
            if calories is None:
                # Items with unknown calories cannot be budgeted; skip rather
                # than assume any value.
                continue
            if high is not None and total_calories + calories > high:
                continue
            selected.append(item)
            total_calories += calories
        if not selected:
            return None
        if low is not None and total_calories < low:
            warnings.append(ResultWarning.PLATE_BELOW_CALORIE_TARGET)
        explanation = (
            "Combines the highest-ranked eligible items that fit your calorie "
            "budget, in ranking order."
        )

    totals, incomplete = _totals(selected)
    if incomplete:
        warnings.append(ResultWarning.PLATE_NUTRIENT_TOTALS_INCOMPLETE)
    if preferences.protein_target_g is not None and (
        totals.protein_g is None or totals.protein_g < preferences.protein_target_g
    ):
        warnings.append(ResultWarning.PLATE_BELOW_PROTEIN_TARGET)

    return PlateSuggestion(
        item_ids=tuple(item.item_id for item in selected),
        item_names=tuple(item.name for item in selected),
        totals=totals,
        warnings=tuple(warnings),
        explanation=explanation,
    )
