"""Import-pipeline enums that are not persisted as database types."""

from __future__ import annotations

from enum import StrEnum

# The 9 nutrients tracked across provided, provider, and calculated nutrition.
# The order is stable and shared by contracts, the calculator, and repositories.
NUTRIENT_FIELDS: tuple[str, ...] = (
    "calories",
    "protein_g",
    "carbohydrates_g",
    "fat_g",
    "saturated_fat_g",
    "fiber_g",
    "sugar_g",
    "sodium_mg",
    "cholesterol_mg",
)


class RecordClassification(StrEnum):
    """Classification of an incoming menu-item record before persistence."""

    NUTRITION_READY = "nutrition_ready"
    RECIPE_READY = "recipe_ready"
    INCOMPLETE = "incomplete"
    INVALID = "invalid"
