"""Stable human-readable explanations for machine-readable codes.

Every code enum is covered by a total mapping (asserted by tests), so a new
code cannot ship without an explanation. Text is deliberately careful: it
never claims medical certainty or allergen safety, and uncertainty wording
("may", "unknown", "not confirmed") is preserved.
"""

from __future__ import annotations

from app.recommendations.enums import (
    CautionReason,
    ExclusionReason,
    PositiveReason,
    ResultWarning,
)

POSITIVE_TEXT: dict[PositiveReason, str] = {
    PositiveReason.HIGH_PROTEIN: "High in protein for a single serving.",
    PositiveReason.PROTEIN_DENSE: "A large share of its calories come from protein.",
    PositiveReason.WITHIN_CALORIE_TARGET: "Fits within your calorie target.",
    PositiveReason.LOW_CALORIE: "Relatively low in calories per serving.",
    PositiveReason.HIGH_FIBER: "A good source of fiber.",
    PositiveReason.LOW_SODIUM: "Low in sodium per serving.",
}

CAUTION_TEXT: dict[CautionReason, str] = {
    CautionReason.MAY_CONTAIN_EXCLUDED_ALLERGEN: (
        "May contain an allergen you excluded; not confirmed safe."
    ),
    CautionReason.ALLERGEN_DATA_INCOMPLETE: (
        "Allergen information is incomplete; this item is not confirmed free of "
        "your excluded allergens."
    ),
    CautionReason.DIETARY_DATA_INCOMPLETE: (
        "Dietary information is incomplete; a required dietary tag could not be "
        "confirmed."
    ),
    CautionReason.UNVERIFIED_DIETARY_TAG: (
        "A dietary tag on this item has not been officially verified."
    ),
    CautionReason.HIGH_SODIUM: "High in sodium per serving.",
    CautionReason.ABOVE_CALORIE_TARGET: "Above your per-item calorie target.",
    CautionReason.NUTRITION_CALCULATED: (
        "Nutrition was calculated from a recipe rather than provided by the source."
    ),
    CautionReason.NUTRITION_ESTIMATED: "Nutrition values are estimates.",
    CautionReason.NUTRITION_INCOMPLETE: (
        "Nutrition data is incomplete or awaiting review; values may change."
    ),
    CautionReason.MISSING_NUTRIENTS: (
        "Some nutrient values are unknown; unknown values are not counted as zero."
    ),
    CautionReason.SERVING_SIZE_UNKNOWN: "Serving size is unknown.",
    CautionReason.AVAILABILITY_UNCERTAIN: "Availability has not been confirmed.",
}

EXCLUSION_TEXT: dict[ExclusionReason, str] = {
    ExclusionReason.ALLERGEN_CONFLICT: (
        "Declared to contain (or possibly contain) an allergen you excluded."
    ),
    ExclusionReason.DIETARY_CONFLICT: (
        "Conflicts with your required or excluded dietary preferences."
    ),
    ExclusionReason.UNAVAILABLE: "Not currently available according to the source.",
    ExclusionReason.USER_EXCLUDED: "You asked to exclude this item.",
    ExclusionReason.UNKNOWN_ALLERGEN_STATUS: (
        "Allergen information is unknown or incomplete, so this item cannot be "
        "confirmed safe for your excluded allergens."
    ),
    ExclusionReason.UNKNOWN_DIETARY_STATUS: (
        "Dietary information is unknown or incomplete, so a required dietary tag "
        "could not be confirmed."
    ),
    ExclusionReason.INSUFFICIENT_NUTRITION_DATA: (
        "Nutrition data is missing or not reliable enough to recommend this item."
    ),
}

WARNING_TEXT: dict[ResultWarning, str] = {
    ResultWarning.NO_ELIGIBLE_ITEMS: (
        "No items met your preferences and safety settings."
    ),
    ResultWarning.ITEMS_EXCLUDED_UNKNOWN_SAFETY_DATA: (
        "Some items were excluded because their allergen or dietary information "
        "is unknown, not because they are confirmed unsafe."
    ),
    ResultWarning.PLATE_NOT_ASSEMBLED: (
        "A plate could not be assembled from the eligible items."
    ),
    ResultWarning.PLATE_NO_CALORIE_TARGET: (
        "No calorie target was set; the plate combines the top-ranked items."
    ),
    ResultWarning.PLATE_BELOW_CALORIE_TARGET: (
        "The assembled plate falls short of your calorie target."
    ),
    ResultWarning.PLATE_BELOW_PROTEIN_TARGET: (
        "The assembled plate falls short of your protein target."
    ),
    ResultWarning.PLATE_NUTRIENT_TOTALS_INCOMPLETE: (
        "Some plate nutrient totals are unknown because item data is incomplete; "
        "unknown values were not counted as zero."
    ),
}


def explain_positives(reasons: tuple[PositiveReason, ...]) -> tuple[str, ...]:
    return tuple(POSITIVE_TEXT[reason] for reason in reasons)


def explain_cautions(cautions: tuple[CautionReason, ...]) -> tuple[str, ...]:
    return tuple(CAUTION_TEXT[caution] for caution in cautions)


def explain_exclusions(reasons: tuple[ExclusionReason, ...]) -> tuple[str, ...]:
    return tuple(EXCLUSION_TEXT[reason] for reason in reasons)


def explain_warnings(warnings: tuple[ResultWarning, ...]) -> tuple[str, ...]:
    return tuple(WARNING_TEXT[warning] for warning in warnings)
