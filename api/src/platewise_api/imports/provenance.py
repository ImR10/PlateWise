"""Provenance helpers: comparing source-provided vs recipe-calculated nutrition.

Both nutrition origins are preserved (never overwritten). When both exist and
are complete, a large calorie discrepancy is *detectable* and flags the
calculated record for review -- without building any review UI.
"""

from __future__ import annotations

from decimal import Decimal

# Relative calorie difference above which we flag for review (25%).
DISCREPANCY_THRESHOLD = Decimal("0.25")


def calorie_discrepancy(
    source_calories: Decimal | None, calculated_calories: Decimal | None
) -> Decimal | None:
    """Return the relative difference in calories, or ``None`` if not comparable."""
    if source_calories is None or calculated_calories is None:
        return None
    if source_calories == 0:
        return None
    return abs(calculated_calories - source_calories) / source_calories


def is_large_discrepancy(
    source_calories: Decimal | None, calculated_calories: Decimal | None
) -> bool:
    """True if source and calculated calories differ beyond the review threshold."""
    diff = calorie_discrepancy(source_calories, calculated_calories)
    return diff is not None and diff > DISCREPANCY_THRESHOLD
