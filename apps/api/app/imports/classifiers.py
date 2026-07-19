"""Record classification.

Each incoming menu item is classified before persistence into one of:

* ``nutrition_ready`` -- usable source nutrition with a serving basis;
* ``recipe_ready``    -- a recipe with enough ingredient/quantity/yield info to
  attempt calculation;
* ``incomplete``      -- partial data (preserved and flagged, never invented);
* ``invalid``         -- structurally unusable.

An item may carry *both* provided nutrition and a recipe; classification returns
the primary label, and the service still processes every path that is present.
"""

from __future__ import annotations

from app.imports.contracts import ImportedMenuItem, ImportedNutrition, ImportedRecipe
from app.imports.enums import NUTRIENT_FIELDS, RecordClassification


def _has_any_nutrient(nutrition: ImportedNutrition) -> bool:
    return any(getattr(nutrition.nutrients, field) is not None for field in NUTRIENT_FIELDS)


def _has_serving_basis(item: ImportedMenuItem, nutrition: ImportedNutrition) -> bool:
    return (
        nutrition.serving_size is not None
        or bool(nutrition.serving_unit)
        or item.serving_size is not None
        or bool(item.serving_unit)
    )


def provided_nutrition_is_usable(item: ImportedMenuItem) -> bool:
    """True if source-provided nutrition has both a serving basis and values."""
    nutrition = item.provided_nutrition
    if nutrition is None:
        return False
    return _has_serving_basis(item, nutrition) and _has_any_nutrient(nutrition)


def recipe_is_ready(recipe: ImportedRecipe | None) -> bool:
    """True if the recipe has enough structure to attempt a calculation."""
    if recipe is None or not recipe.ingredients:
        return False
    if recipe.servings is None or recipe.servings <= 0:
        return False
    # At least one ingredient must carry a quantity and unit to be calculable.
    return any(ing.quantity is not None and ing.unit for ing in recipe.ingredients)


def classify(item: ImportedMenuItem) -> RecordClassification:
    """Classify a menu item record."""
    if not item.name.strip():
        return RecordClassification.INVALID

    if provided_nutrition_is_usable(item):
        return RecordClassification.NUTRITION_READY
    if recipe_is_ready(item.recipe):
        return RecordClassification.RECIPE_READY

    # Partial data is preserved for review rather than invented or discarded.
    has_partial_nutrition = item.provided_nutrition is not None
    has_partial_recipe = item.recipe is not None and bool(item.recipe.ingredients)
    if has_partial_nutrition or has_partial_recipe:
        return RecordClassification.INCOMPLETE

    # A bare catalog item with no nutrition and no recipe is still preserved.
    return RecordClassification.INCOMPLETE
