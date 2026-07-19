"""Deterministic, transparent scoring policy.

Score model
-----------
Each eligible item is scored on bounded dimensions (components), every
component producing a ``Decimal`` in ``[0, 1]`` or ``None`` when its inputs
are unknown — a missing nutrient never contributes a zero score. The total is
the weighted mean of the *available* components rescaled to **0-100**:

    total = 100 x sum(w_i * c_i) / sum(w_i)   over available components

Weights are per-goal, centralized in :data:`GOAL_WEIGHTS`, and each goal's
weights sum to exactly 1 (validated at import time). All reference values are
named module constants — no scattered magic numbers. Data confidence is both a
scored component and a separate 0-1 value used as the second ranking
tie-breaker.

Changing any weight, reference, or formula must bump
:data:`SCORING_POLICY_VERSION`.
"""

from __future__ import annotations

from decimal import Decimal

from app.db.enums import NutritionProvenance, NutritionReviewStatus, OfferingStatus
from app.imports.decimal_utils import ROUNDING
from app.recommendations.contracts import (
    ComponentScore,
    RecommendationItem,
    ScoreBreakdown,
    UserPreferences,
)
from app.recommendations.enums import (
    CautionReason,
    GoalType,
    PositiveReason,
    ScoreComponent,
)

SCORING_POLICY_VERSION = "1.0.0"

_ZERO = Decimal("0")
_ONE = Decimal("1")
_HUNDRED = Decimal("100")

#: Quantization of component/confidence values (4 dp) and totals (2 dp),
#: rounding ``ROUND_HALF_UP`` per the repository Decimal policy.
COMPONENT_EXP = Decimal("0.0001")
SCORE_EXP = Decimal("0.01")
CONFIDENCE_EXP = Decimal("0.01")

# --- Reference values (per single item serving) ----------------------------

#: Plate-level targets are divided by this to obtain a per-item target.
PLATE_ITEM_COUNT = Decimal("3")
#: Grams of protein at which protein adequacy reaches 1.0 (no user target).
PROTEIN_REFERENCE_G = Decimal("30")
#: Calories contributed per gram of protein (Atwater factor).
CALORIES_PER_PROTEIN_GRAM = Decimal("4")
#: Fraction of calories from protein at which protein density reaches 1.0.
PROTEIN_DENSITY_TARGET = Decimal("0.30")
#: Calories at which the calorie-moderation component reaches 0.
CALORIE_MODERATION_REFERENCE_KCAL = Decimal("800")
#: Grams of fiber at which fiber adequacy reaches 1.0.
FIBER_REFERENCE_G = Decimal("8")
#: Milligrams of sodium at which the sodium-moderation component reaches 0.
SODIUM_REFERENCE_MG = Decimal("1500")
#: Sodium above this per serving earns a HIGH_SODIUM caution.
HIGH_SODIUM_CAUTION_MG = Decimal("800")

# --- Positive-reason thresholds (component score in [0, 1]) ----------------

HIGH_PROTEIN_THRESHOLD = Decimal("0.80")
PROTEIN_DENSE_THRESHOLD = Decimal("0.80")
LOW_CALORIE_THRESHOLD = Decimal("0.70")
HIGH_FIBER_THRESHOLD = Decimal("0.75")
LOW_SODIUM_THRESHOLD = Decimal("0.80")

# --- Confidence factors (multiplied together, then quantized) --------------

PROVENANCE_CONFIDENCE: dict[NutritionProvenance, Decimal] = {
    NutritionProvenance.SOURCE_PROVIDED: Decimal("1.00"),
    NutritionProvenance.MANUALLY_ENTERED: Decimal("0.95"),
    NutritionProvenance.RECIPE_CALCULATED: Decimal("0.85"),
    NutritionProvenance.ESTIMATED: Decimal("0.70"),
}
UNKNOWN_PROVENANCE_CONFIDENCE = Decimal("0.50")
INCOMPLETE_NUTRITION_FACTOR = Decimal("0.60")
NEEDS_REVIEW_FACTOR = Decimal("0.85")
SERVING_UNKNOWN_FACTOR = Decimal("0.90")
AVAILABILITY_CONFIDENCE: dict[OfferingStatus, Decimal] = {
    OfferingStatus.AVAILABLE: Decimal("1.00"),
    OfferingStatus.SCHEDULED: Decimal("0.95"),
    OfferingStatus.UNKNOWN: Decimal("0.85"),
}
UNCERTAIN_AVAILABILITY_CONFIDENCE = Decimal("0.85")
#: Confidence floor when every core nutrient is missing; scales linearly with
#: the fraction of core nutrients that are known.
MISSING_NUTRIENT_FLOOR = Decimal("0.50")
#: Nutrients whose presence drives the missing-data confidence factor and the
#: MISSING_NUTRIENTS caution.
CORE_NUTRIENT_FIELDS: tuple[str, ...] = (
    "calories",
    "protein_g",
    "carbohydrates_g",
    "fat_g",
    "fiber_g",
    "sodium_mg",
)

# --- Per-goal component weights (each goal sums to exactly 1) --------------

_BALANCED_WEIGHTS: dict[ScoreComponent, Decimal] = {
    ScoreComponent.PROTEIN_ADEQUACY: Decimal("0.15"),
    ScoreComponent.PROTEIN_DENSITY: Decimal("0.10"),
    ScoreComponent.CALORIE_FIT: Decimal("0.10"),
    ScoreComponent.CALORIE_MODERATION: Decimal("0.15"),
    ScoreComponent.FIBER_ADEQUACY: Decimal("0.20"),
    ScoreComponent.SODIUM_MODERATION: Decimal("0.20"),
    ScoreComponent.DATA_CONFIDENCE: Decimal("0.10"),
}

GOAL_WEIGHTS: dict[GoalType, dict[ScoreComponent, Decimal]] = {
    GoalType.HIGH_PROTEIN: {
        ScoreComponent.PROTEIN_ADEQUACY: Decimal("0.35"),
        ScoreComponent.PROTEIN_DENSITY: Decimal("0.30"),
        ScoreComponent.CALORIE_FIT: Decimal("0.05"),
        ScoreComponent.CALORIE_MODERATION: Decimal("0.05"),
        ScoreComponent.FIBER_ADEQUACY: Decimal("0.05"),
        ScoreComponent.SODIUM_MODERATION: Decimal("0.10"),
        ScoreComponent.DATA_CONFIDENCE: Decimal("0.10"),
    },
    GoalType.LOWER_CALORIE: {
        ScoreComponent.PROTEIN_ADEQUACY: Decimal("0.05"),
        ScoreComponent.PROTEIN_DENSITY: Decimal("0.10"),
        ScoreComponent.CALORIE_FIT: Decimal("0.15"),
        ScoreComponent.CALORIE_MODERATION: Decimal("0.40"),
        ScoreComponent.FIBER_ADEQUACY: Decimal("0.10"),
        ScoreComponent.SODIUM_MODERATION: Decimal("0.10"),
        ScoreComponent.DATA_CONFIDENCE: Decimal("0.10"),
    },
    GoalType.BALANCED: _BALANCED_WEIGHTS,
    GoalType.HIGH_FIBER: {
        ScoreComponent.PROTEIN_ADEQUACY: Decimal("0.10"),
        ScoreComponent.PROTEIN_DENSITY: Decimal("0.05"),
        ScoreComponent.CALORIE_FIT: Decimal("0.05"),
        ScoreComponent.CALORIE_MODERATION: Decimal("0.10"),
        ScoreComponent.FIBER_ADEQUACY: Decimal("0.45"),
        ScoreComponent.SODIUM_MODERATION: Decimal("0.15"),
        ScoreComponent.DATA_CONFIDENCE: Decimal("0.10"),
    },
    GoalType.LOWER_SODIUM: {
        ScoreComponent.PROTEIN_ADEQUACY: Decimal("0.10"),
        ScoreComponent.PROTEIN_DENSITY: Decimal("0.05"),
        ScoreComponent.CALORIE_FIT: Decimal("0.05"),
        ScoreComponent.CALORIE_MODERATION: Decimal("0.15"),
        ScoreComponent.FIBER_ADEQUACY: Decimal("0.10"),
        ScoreComponent.SODIUM_MODERATION: Decimal("0.45"),
        ScoreComponent.DATA_CONFIDENCE: Decimal("0.10"),
    },
    # Vegetarian is enforced by the hard dietary filter; scoring is balanced.
    GoalType.VEGETARIAN: _BALANCED_WEIGHTS,
}


def _validate_weights() -> None:
    for goal in GoalType:
        weights = GOAL_WEIGHTS.get(goal)
        if weights is None:
            raise ValueError(f"missing scoring weights for goal {goal!r}")
        total = sum(weights.values(), _ZERO)
        if total != _ONE:
            raise ValueError(f"weights for goal {goal!r} sum to {total}, expected 1")


_validate_weights()


def _clamp01(value: Decimal) -> Decimal:
    return min(max(value, _ZERO), _ONE)


# --- Component functions ---------------------------------------------------


def _per_item(value: Decimal | None) -> Decimal | None:
    """Divide a plate-level target into a per-item target."""
    if value is None:
        return None
    return value / PLATE_ITEM_COUNT


def protein_adequacy(
    protein_g: Decimal | None, preferences: UserPreferences
) -> Decimal | None:
    if protein_g is None:
        return None
    reference = _per_item(preferences.protein_target_g) or PROTEIN_REFERENCE_G
    return _clamp01(protein_g / reference)


def protein_density(
    protein_g: Decimal | None, calories: Decimal | None
) -> Decimal | None:
    if protein_g is None or calories is None or calories <= 0:
        return None
    fraction = protein_g * CALORIES_PER_PROTEIN_GRAM / calories
    return _clamp01(fraction / PROTEIN_DENSITY_TARGET)


def calorie_fit(calories: Decimal | None, preferences: UserPreferences) -> Decimal | None:
    """Closeness to the user's per-item calorie target or range.

    1.0 inside the range (or exactly at the target) with a linear falloff
    outside, hitting 0 at 100% relative distance. ``None`` when the user set
    no calorie target/range or the item's calories are unknown.
    """
    if calories is None:
        return None
    low = _per_item(preferences.calorie_min)
    high = _per_item(preferences.calorie_max)
    if low is None and high is None:
        target = _per_item(preferences.calorie_target)
        if target is None:
            return None
        low = high = target
    if low is not None and calories < low:
        return _clamp01(_ONE - (low - calories) / low)
    if high is not None and calories > high:
        return _clamp01(_ONE - (calories - high) / high)
    return _ONE


def calorie_moderation(calories: Decimal | None) -> Decimal | None:
    if calories is None:
        return None
    return _clamp01(_ONE - calories / CALORIE_MODERATION_REFERENCE_KCAL)


def fiber_adequacy(fiber_g: Decimal | None) -> Decimal | None:
    if fiber_g is None:
        return None
    return _clamp01(fiber_g / FIBER_REFERENCE_G)


def sodium_moderation(sodium_mg: Decimal | None) -> Decimal | None:
    if sodium_mg is None:
        return None
    return _clamp01(_ONE - sodium_mg / SODIUM_REFERENCE_MG)


def compute_confidence(item: RecommendationItem) -> Decimal:
    """Data confidence in [0, 1] from provenance, completeness, and status."""
    nutrition = item.nutrition
    if nutrition is None:  # defensive: filters exclude such items first
        return _ZERO

    if nutrition.provenance is None:
        confidence = UNKNOWN_PROVENANCE_CONFIDENCE
    else:
        confidence = PROVENANCE_CONFIDENCE[nutrition.provenance]

    if not nutrition.is_complete:
        confidence *= INCOMPLETE_NUTRITION_FACTOR
    if nutrition.review_status is NutritionReviewStatus.NEEDS_REVIEW:
        confidence *= NEEDS_REVIEW_FACTOR
    if nutrition.serving_size is None and nutrition.serving_unit is None:
        confidence *= SERVING_UNKNOWN_FACTOR

    known = sum(
        1 for field in CORE_NUTRIENT_FIELDS if getattr(nutrition.nutrients, field) is not None
    )
    fraction = Decimal(known) / Decimal(len(CORE_NUTRIENT_FIELDS))
    confidence *= MISSING_NUTRIENT_FLOOR + (_ONE - MISSING_NUTRIENT_FLOOR) * fraction

    confidence *= AVAILABILITY_CONFIDENCE.get(
        item.availability, UNCERTAIN_AVAILABILITY_CONFIDENCE
    )
    return _clamp01(confidence).quantize(CONFIDENCE_EXP, rounding=ROUNDING)


def _data_cautions(item: RecommendationItem) -> list[CautionReason]:
    cautions: list[CautionReason] = []
    nutrition = item.nutrition
    if nutrition is None:
        return cautions
    if nutrition.provenance is NutritionProvenance.RECIPE_CALCULATED:
        cautions.append(CautionReason.NUTRITION_CALCULATED)
    if nutrition.provenance is NutritionProvenance.ESTIMATED:
        cautions.append(CautionReason.NUTRITION_ESTIMATED)
    if (
        not nutrition.is_complete
        or nutrition.review_status is NutritionReviewStatus.NEEDS_REVIEW
    ):
        cautions.append(CautionReason.NUTRITION_INCOMPLETE)
    if any(
        getattr(nutrition.nutrients, field) is None for field in CORE_NUTRIENT_FIELDS
    ):
        cautions.append(CautionReason.MISSING_NUTRIENTS)
    if nutrition.serving_size is None and nutrition.serving_unit is None:
        cautions.append(CautionReason.SERVING_SIZE_UNKNOWN)
    if item.availability is OfferingStatus.UNKNOWN:
        cautions.append(CautionReason.AVAILABILITY_UNCERTAIN)
    return cautions


def score_item(item: RecommendationItem, preferences: UserPreferences) -> ScoreBreakdown:
    """Score one eligible item. Pure and deterministic."""
    nutrition = item.nutrition
    nutrients = nutrition.nutrients if nutrition is not None else None
    calories = nutrients.calories if nutrients is not None else None
    protein = nutrients.protein_g if nutrients is not None else None
    fiber = nutrients.fiber_g if nutrients is not None else None
    sodium = nutrients.sodium_mg if nutrients is not None else None

    confidence = compute_confidence(item)
    raw_components: dict[ScoreComponent, Decimal | None] = {
        ScoreComponent.PROTEIN_ADEQUACY: protein_adequacy(protein, preferences),
        ScoreComponent.PROTEIN_DENSITY: protein_density(protein, calories),
        ScoreComponent.CALORIE_FIT: calorie_fit(calories, preferences),
        ScoreComponent.CALORIE_MODERATION: calorie_moderation(calories),
        ScoreComponent.FIBER_ADEQUACY: fiber_adequacy(fiber),
        ScoreComponent.SODIUM_MODERATION: sodium_moderation(sodium),
        ScoreComponent.DATA_CONFIDENCE: confidence,
    }

    weights = GOAL_WEIGHTS[preferences.goal]
    available = [
        (component, weights[component], score)
        for component, score in raw_components.items()
        if score is not None
    ]
    total_weight = sum((weight for _, weight, _ in available), _ZERO)
    if total_weight == 0:  # defensive: DATA_CONFIDENCE is always available
        total_score = _ZERO.quantize(SCORE_EXP, rounding=ROUNDING)
    else:
        weighted = sum((weight * score for _, weight, score in available), _ZERO)
        total_score = _clamp01(weighted / total_weight)
        total_score = (total_score * _HUNDRED).quantize(SCORE_EXP, rounding=ROUNDING)

    components = tuple(
        ComponentScore(
            component=component,
            weight=weight,
            score=score.quantize(COMPONENT_EXP, rounding=ROUNDING),
        )
        for component, weight, score in available
    )

    positive: list[PositiveReason] = []
    if (
        raw_components[ScoreComponent.PROTEIN_ADEQUACY] is not None
        and raw_components[ScoreComponent.PROTEIN_ADEQUACY] >= HIGH_PROTEIN_THRESHOLD
    ):
        positive.append(PositiveReason.HIGH_PROTEIN)
    if (
        raw_components[ScoreComponent.PROTEIN_DENSITY] is not None
        and raw_components[ScoreComponent.PROTEIN_DENSITY] >= PROTEIN_DENSE_THRESHOLD
    ):
        positive.append(PositiveReason.PROTEIN_DENSE)
    if raw_components[ScoreComponent.CALORIE_FIT] == _ONE:
        positive.append(PositiveReason.WITHIN_CALORIE_TARGET)
    if (
        raw_components[ScoreComponent.CALORIE_MODERATION] is not None
        and raw_components[ScoreComponent.CALORIE_MODERATION] >= LOW_CALORIE_THRESHOLD
    ):
        positive.append(PositiveReason.LOW_CALORIE)
    if (
        raw_components[ScoreComponent.FIBER_ADEQUACY] is not None
        and raw_components[ScoreComponent.FIBER_ADEQUACY] >= HIGH_FIBER_THRESHOLD
    ):
        positive.append(PositiveReason.HIGH_FIBER)
    if (
        raw_components[ScoreComponent.SODIUM_MODERATION] is not None
        and raw_components[ScoreComponent.SODIUM_MODERATION] >= LOW_SODIUM_THRESHOLD
    ):
        positive.append(PositiveReason.LOW_SODIUM)

    cautions = _data_cautions(item)
    if sodium is not None and sodium > HIGH_SODIUM_CAUTION_MG:
        cautions.append(CautionReason.HIGH_SODIUM)
    high = _per_item(preferences.calorie_max)
    if high is None and preferences.calorie_min is None:
        high = _per_item(preferences.calorie_target)
    if calories is not None and high is not None and calories > high:
        cautions.append(CautionReason.ABOVE_CALORIE_TARGET)

    ordered_positive = tuple(r for r in PositiveReason if r in set(positive))
    ordered_cautions = tuple(c for c in CautionReason if c in set(cautions))
    return ScoreBreakdown(
        total_score=total_score,
        confidence=confidence,
        components=components,
        positive_reasons=ordered_positive,
        cautions=ordered_cautions,
    )
