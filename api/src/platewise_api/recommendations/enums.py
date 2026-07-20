"""Recommendation-domain enums and machine-readable codes (not persisted).

Goal and mode values are lowercase like the rest of the repository's setting
enums. Reason/caution/warning codes are UPPERCASE because they are emitted as
machine-readable codes in results (matching the milestone contract examples,
e.g. ``ALLERGEN_CONFLICT``); no equivalent enums exist elsewhere in the repo.
"""

from __future__ import annotations

from enum import StrEnum


class GoalType(StrEnum):
    """Explicit, structured user goals supported by the MVP scorer."""

    HIGH_PROTEIN = "high_protein"
    LOWER_CALORIE = "lower_calorie"
    BALANCED = "balanced"
    HIGH_FIBER = "high_fiber"
    LOWER_SODIUM = "lower_sodium"
    VEGETARIAN = "vegetarian"


class SafetyMode(StrEnum):
    """How unknown safety metadata is handled.

    ``strict`` (the default) excludes items whose allergen/dietary status
    cannot be confirmed when the user's preferences depend on it — unknown is
    never treated as safe. ``permissive`` keeps such items but surfaces
    explicit cautions.
    """

    STRICT = "strict"
    PERMISSIVE = "permissive"


class ExclusionReason(StrEnum):
    """Machine-readable reason an item was excluded before scoring."""

    ALLERGEN_CONFLICT = "ALLERGEN_CONFLICT"
    DIETARY_CONFLICT = "DIETARY_CONFLICT"
    UNAVAILABLE = "UNAVAILABLE"
    USER_EXCLUDED = "USER_EXCLUDED"
    UNKNOWN_ALLERGEN_STATUS = "UNKNOWN_ALLERGEN_STATUS"
    UNKNOWN_DIETARY_STATUS = "UNKNOWN_DIETARY_STATUS"
    INSUFFICIENT_NUTRITION_DATA = "INSUFFICIENT_NUTRITION_DATA"


class ScoreComponent(StrEnum):
    """Identifier of one bounded [0, 1] scoring dimension."""

    PROTEIN_ADEQUACY = "protein_adequacy"
    PROTEIN_DENSITY = "protein_density"
    CALORIE_FIT = "calorie_fit"
    CALORIE_MODERATION = "calorie_moderation"
    FIBER_ADEQUACY = "fiber_adequacy"
    SODIUM_MODERATION = "sodium_moderation"
    DATA_CONFIDENCE = "data_confidence"


class PositiveReason(StrEnum):
    """Machine-readable positive reason attached to a recommendation."""

    HIGH_PROTEIN = "HIGH_PROTEIN"
    PROTEIN_DENSE = "PROTEIN_DENSE"
    WITHIN_CALORIE_TARGET = "WITHIN_CALORIE_TARGET"
    LOW_CALORIE = "LOW_CALORIE"
    HIGH_FIBER = "HIGH_FIBER"
    LOW_SODIUM = "LOW_SODIUM"


class CautionReason(StrEnum):
    """Machine-readable caution attached to a recommendation.

    Cautions never assert safety; they surface risk or reduced certainty.
    """

    MAY_CONTAIN_EXCLUDED_ALLERGEN = "MAY_CONTAIN_EXCLUDED_ALLERGEN"
    ALLERGEN_DATA_INCOMPLETE = "ALLERGEN_DATA_INCOMPLETE"
    DIETARY_DATA_INCOMPLETE = "DIETARY_DATA_INCOMPLETE"
    UNVERIFIED_DIETARY_TAG = "UNVERIFIED_DIETARY_TAG"
    HIGH_SODIUM = "HIGH_SODIUM"
    ABOVE_CALORIE_TARGET = "ABOVE_CALORIE_TARGET"
    NUTRITION_CALCULATED = "NUTRITION_CALCULATED"
    NUTRITION_ESTIMATED = "NUTRITION_ESTIMATED"
    NUTRITION_INCOMPLETE = "NUTRITION_INCOMPLETE"
    MISSING_NUTRIENTS = "MISSING_NUTRIENTS"
    SERVING_SIZE_UNKNOWN = "SERVING_SIZE_UNKNOWN"
    AVAILABILITY_UNCERTAIN = "AVAILABILITY_UNCERTAIN"


class ResultWarning(StrEnum):
    """Machine-readable warning attached to a whole recommendation result."""

    NO_ELIGIBLE_ITEMS = "NO_ELIGIBLE_ITEMS"
    ITEMS_EXCLUDED_UNKNOWN_SAFETY_DATA = "ITEMS_EXCLUDED_UNKNOWN_SAFETY_DATA"
    PLATE_NOT_ASSEMBLED = "PLATE_NOT_ASSEMBLED"
    PLATE_NO_CALORIE_TARGET = "PLATE_NO_CALORIE_TARGET"
    PLATE_BELOW_CALORIE_TARGET = "PLATE_BELOW_CALORIE_TARGET"
    PLATE_BELOW_PROTEIN_TARGET = "PLATE_BELOW_PROTEIN_TARGET"
    PLATE_NUTRIENT_TOTALS_INCOMPLETE = "PLATE_NUTRIENT_TOTALS_INCOMPLETE"
