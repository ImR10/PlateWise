"""Deterministic in-memory builders for recommendation-engine tests.

No database, network, or filesystem access. Defaults describe a well-formed
item (complete source-provided nutrition, available, no allergens declared);
tests override only what each scenario needs.
"""

from __future__ import annotations

from decimal import Decimal

from platewise_db.enums import (
    AllergenDeclarationType,
    NutritionProvenance,
    NutritionReviewStatus,
    OfferingStatus,
    ProvenanceSourceType,
)

from platewise_api.imports.contracts import NutrientValues
from platewise_api.recommendations.contracts import (
    AllergenInfo,
    DietaryTagInfo,
    RecommendationItem,
    RecommendationNutrition,
    UserPreferences,
)

_UNSET = object()


def dec(value: object) -> Decimal | None:
    """``None`` passes through; anything else becomes an exact ``Decimal``."""
    if value is None:
        return None
    return Decimal(str(value))


def make_nutrition(
    *,
    calories: object = "450",
    protein_g: object = "25",
    carbohydrates_g: object = "40",
    fat_g: object = "15",
    saturated_fat_g: object = "4",
    fiber_g: object = "5",
    sugar_g: object = "6",
    sodium_mg: object = "500",
    cholesterol_mg: object = "70",
    provenance: NutritionProvenance | None = NutritionProvenance.SOURCE_PROVIDED,
    is_complete: bool = True,
    review_status: NutritionReviewStatus = NutritionReviewStatus.NOT_REQUIRED,
    serving_size: object = "1",
    serving_unit: str | None = "serving",
) -> RecommendationNutrition:
    return RecommendationNutrition(
        serving_size=dec(serving_size),
        serving_unit=serving_unit,
        nutrients=NutrientValues(
            calories=dec(calories),
            protein_g=dec(protein_g),
            carbohydrates_g=dec(carbohydrates_g),
            fat_g=dec(fat_g),
            saturated_fat_g=dec(saturated_fat_g),
            fiber_g=dec(fiber_g),
            sugar_g=dec(sugar_g),
            sodium_mg=dec(sodium_mg),
            cholesterol_mg=dec(cholesterol_mg),
        ),
        provenance=provenance,
        is_complete=is_complete,
        review_status=review_status,
    )


def allergen(
    name: str, declaration: AllergenDeclarationType = AllergenDeclarationType.CONTAINS
) -> AllergenInfo:
    return AllergenInfo(name=name, declaration=declaration)


def tag(
    name: str,
    source_type: ProvenanceSourceType = ProvenanceSourceType.OFFICIAL,
    confidence: object = None,
) -> DietaryTagInfo:
    return DietaryTagInfo(name=name, source_type=source_type, confidence=dec(confidence))


def make_item(
    item_id: str = "item-1",
    name: str = "Grilled Chicken",
    *,
    nutrition: object = _UNSET,
    allergens: tuple[AllergenInfo, ...] = (),
    allergen_data_complete: bool = False,
    dietary_tags: tuple[DietaryTagInfo, ...] = (),
    dietary_tag_data_complete: bool = False,
    availability: OfferingStatus = OfferingStatus.AVAILABLE,
    description: str | None = None,
) -> RecommendationItem:
    if nutrition is _UNSET:
        nutrition = make_nutrition()
    return RecommendationItem(
        item_id=item_id,
        name=name,
        description=description,
        nutrition=nutrition,  # type: ignore[arg-type]
        allergens=allergens,
        allergen_data_complete=allergen_data_complete,
        dietary_tags=dietary_tags,
        dietary_tag_data_complete=dietary_tag_data_complete,
        availability=availability,
    )


def prefs(**kwargs: object) -> UserPreferences:
    return UserPreferences(**kwargs)  # type: ignore[arg-type]
