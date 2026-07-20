"""Recipe nutrition calculation.

Aggregates resolved ingredient contributions and divides by recipe yield to get
per-serving nutrition. All arithmetic is exact ``Decimal``; values are quantized
only at the end (the persistence boundary).

Integrity rules enforced here:

* A missing nutrient on any contributing food makes that nutrient *unknown*
  (``None``) for the whole recipe -- it is never summed as zero.
* An unresolved ingredient (that is not an intentional non-nutritive exclusion)
  makes the calculation ``partial`` and never authoritative; its (absent)
  contribution is not counted as zero.
* Missing/zero servings makes the calculation ``failed`` (no per-serving basis).
* Partial results still retain the computed subtotals for review, but
  ``is_complete`` is ``False``.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

from platewise_db.constants import NUTRIENT_FIELDS
from platewise_db.decimal_utils import quantize_nutrient
from platewise_db.enums import CalculationStatus, IngredientResolutionStatus

from platewise_api.imports.recipes.resolver import ResolvedIngredient

CALCULATION_VERSION = "recipe-calc-1"


@dataclass(frozen=True)
class CalculatedNutrition:
    """Per-serving recipe nutrition plus calculation provenance/status."""

    per_serving: dict[str, Decimal | None]
    status: CalculationStatus
    is_complete: bool
    servings: Decimal | None
    resolved_count: int
    unresolved_count: int
    excluded_count: int
    calculation_version: str = CALCULATION_VERSION
    reasons: tuple[str, ...] = ()


def _recipe_totals(
    contributing: Sequence[ResolvedIngredient],
) -> tuple[dict[str, Decimal | None], bool]:
    """Return per-nutrient recipe totals and whether every nutrient is known.

    A nutrient total is ``None`` (unknown) if *any* contributing food lacks it.
    """
    totals: dict[str, Decimal | None] = {}
    all_nutrients_known = True
    for nutrient in NUTRIENT_FIELDS:
        running = Decimal("0")
        known = True
        for item in contributing:
            assert item.provider_food is not None and item.grams is not None
            per_ref = getattr(item.provider_food.nutrients, nutrient)
            if per_ref is None:
                known = False
                break
            running += per_ref * item.grams / item.provider_food.reference_grams
        if known:
            totals[nutrient] = running
        else:
            totals[nutrient] = None
            all_nutrients_known = False
    return totals, all_nutrients_known


def calculate_recipe_nutrition(
    servings: Decimal | None, resolved: Sequence[ResolvedIngredient]
) -> CalculatedNutrition:
    """Calculate per-serving nutrition from resolved ingredients and yield."""
    contributing = [item for item in resolved if item.contributes_nutrition]
    excluded = [
        item
        for item in resolved
        if item.status == IngredientResolutionStatus.EXCLUDED_NON_NUTRITIVE
    ]
    unresolved = [
        item
        for item in resolved
        if item.status
        not in (
            IngredientResolutionStatus.RESOLVED,
            IngredientResolutionStatus.EXCLUDED_NON_NUTRITIVE,
        )
    ]

    reasons: list[str] = []
    empty_per_serving: dict[str, Decimal | None] = {n: None for n in NUTRIENT_FIELDS}

    # Failure: nothing to sum, or no valid per-serving divisor.
    if not contributing:
        reasons.append("no resolved ingredients contribute nutrition")
        return CalculatedNutrition(
            per_serving=empty_per_serving,
            status=CalculationStatus.FAILED,
            is_complete=False,
            servings=servings,
            resolved_count=len(contributing),
            unresolved_count=len(unresolved),
            excluded_count=len(excluded),
            reasons=tuple(reasons),
        )
    if servings is None or servings <= 0:
        reasons.append("recipe yield/servings missing or non-positive")
        return CalculatedNutrition(
            per_serving=empty_per_serving,
            status=CalculationStatus.FAILED,
            is_complete=False,
            servings=servings,
            resolved_count=len(contributing),
            unresolved_count=len(unresolved),
            excluded_count=len(excluded),
            reasons=tuple(reasons),
        )

    totals, all_nutrients_known = _recipe_totals(contributing)

    per_serving: dict[str, Decimal | None] = {}
    for nutrient, total in totals.items():
        per_serving[nutrient] = None if total is None else quantize_nutrient(total / servings)

    if unresolved:
        reasons.append(f"{len(unresolved)} ingredient line(s) unresolved")
    if not all_nutrients_known:
        reasons.append("one or more nutrients unknown for a contributing food")

    is_complete = not unresolved and all_nutrients_known
    status = CalculationStatus.COMPLETE if is_complete else CalculationStatus.PARTIAL

    return CalculatedNutrition(
        per_serving=per_serving,
        status=status,
        is_complete=is_complete,
        servings=servings,
        resolved_count=len(contributing),
        unresolved_count=len(unresolved),
        excluded_count=len(excluded),
        reasons=tuple(reasons),
    )
