"""Deterministic scoring tests (no database)."""

from __future__ import annotations

from decimal import Decimal

import recommendation_fixtures as fx

from app.db.enums import NutritionProvenance, OfferingStatus
from app.recommendations.contracts import RecommendationItem
from app.recommendations.enums import (
    CautionReason,
    GoalType,
    PositiveReason,
    ScoreComponent,
)
from app.recommendations.scoring import (
    GOAL_WEIGHTS,
    HIGH_SODIUM_CAUTION_MG,
    compute_confidence,
    score_item,
)


def _score(item: RecommendationItem, **pref_kwargs: object) -> Decimal:
    return score_item(item, fx.prefs(**pref_kwargs)).total_score


def test_high_protein_item_scores_higher_for_high_protein_goal() -> None:
    high = fx.make_item("h", nutrition=fx.make_nutrition(protein_g="40"))
    low = fx.make_item("l", nutrition=fx.make_nutrition(protein_g="10"))
    assert _score(high, goal=GoalType.HIGH_PROTEIN) > _score(low, goal=GoalType.HIGH_PROTEIN)


def test_lower_calorie_item_scores_higher_for_lower_calorie_goal() -> None:
    light = fx.make_item("light", nutrition=fx.make_nutrition(calories="300"))
    heavy = fx.make_item("heavy", nutrition=fx.make_nutrition(calories="700"))
    assert _score(light, goal=GoalType.LOWER_CALORIE) > _score(
        heavy, goal=GoalType.LOWER_CALORIE
    )


def test_fiber_affects_high_fiber_goal() -> None:
    fibrous = fx.make_item("f", nutrition=fx.make_nutrition(fiber_g="8"))
    plain = fx.make_item("p", nutrition=fx.make_nutrition(fiber_g="1"))
    assert _score(fibrous, goal=GoalType.HIGH_FIBER) > _score(plain, goal=GoalType.HIGH_FIBER)


def test_sodium_penalty_lowers_score() -> None:
    salty = fx.make_item("s", nutrition=fx.make_nutrition(sodium_mg="1400"))
    mild = fx.make_item("m", nutrition=fx.make_nutrition(sodium_mg="200"))
    for goal in (GoalType.LOWER_SODIUM, GoalType.BALANCED):
        assert _score(mild, goal=goal) > _score(salty, goal=goal)

    breakdown = score_item(salty, fx.prefs())
    assert Decimal("1400") > HIGH_SODIUM_CAUTION_MG
    assert CautionReason.HIGH_SODIUM in breakdown.cautions


def test_balanced_goal_does_not_over_reward_one_nutrient() -> None:
    protein_monster = fx.make_item(
        "monster",
        nutrition=fx.make_nutrition(
            calories="500", protein_g="60", fiber_g="0", sodium_mg="1400"
        ),
    )
    moderate = fx.make_item(
        "moderate",
        nutrition=fx.make_nutrition(
            calories="400", protein_g="15", fiber_g="8", sodium_mg="200"
        ),
    )
    # The one-dimensional item wins its own goal but not the balanced goal.
    assert _score(protein_monster, goal=GoalType.HIGH_PROTEIN) > _score(
        moderate, goal=GoalType.HIGH_PROTEIN
    )
    assert _score(moderate, goal=GoalType.BALANCED) > _score(
        protein_monster, goal=GoalType.BALANCED
    )


def test_source_provided_complete_nutrition_has_full_confidence() -> None:
    item = fx.make_item(availability=OfferingStatus.AVAILABLE)
    assert compute_confidence(item) == Decimal("1.00")


def test_calculated_and_incomplete_nutrition_reduce_confidence() -> None:
    calculated = fx.make_item(
        nutrition=fx.make_nutrition(provenance=NutritionProvenance.RECIPE_CALCULATED)
    )
    assert compute_confidence(calculated) == Decimal("0.85")

    incomplete = fx.make_item(
        nutrition=fx.make_nutrition(
            provenance=NutritionProvenance.RECIPE_CALCULATED, is_complete=False
        )
    )
    # 0.85 (calculated) x 0.60 (incomplete) = 0.51
    assert compute_confidence(incomplete) == Decimal("0.51")

    breakdown = score_item(incomplete, fx.prefs(safety_mode="permissive"))
    assert CautionReason.NUTRITION_CALCULATED in breakdown.cautions
    assert CautionReason.NUTRITION_INCOMPLETE in breakdown.cautions


def test_missing_values_do_not_behave_as_zero() -> None:
    missing = fx.make_item("missing", nutrition=fx.make_nutrition(protein_g=None))
    zero = fx.make_item("zero", nutrition=fx.make_nutrition(protein_g="0"))

    missing_breakdown = score_item(missing, fx.prefs(goal=GoalType.HIGH_PROTEIN))
    zero_breakdown = score_item(zero, fx.prefs(goal=GoalType.HIGH_PROTEIN))

    # Missing protein: the protein components are absent, not scored as zero.
    missing_components = {c.component for c in missing_breakdown.components}
    assert ScoreComponent.PROTEIN_ADEQUACY not in missing_components
    assert ScoreComponent.PROTEIN_DENSITY not in missing_components
    assert CautionReason.MISSING_NUTRIENTS in missing_breakdown.cautions

    # An explicit zero is penalized; an unknown value is not.
    assert missing_breakdown.total_score > zero_breakdown.total_score


def test_weights_are_bounded_and_complete() -> None:
    for goal in GoalType:
        weights = GOAL_WEIGHTS[goal]
        assert set(weights) == set(ScoreComponent)
        assert sum(weights.values()) == Decimal("1")
        assert all(Decimal("0") <= weight <= Decimal("1") for weight in weights.values())


def test_scores_are_bounded_and_deterministic() -> None:
    best = fx.make_item(
        "best",
        nutrition=fx.make_nutrition(
            calories="0", protein_g="99", fiber_g="99", sodium_mg="0"
        ),
    )
    worst = fx.make_item(
        "worst",
        nutrition=fx.make_nutrition(
            calories="5000", protein_g="0", fiber_g="0", sodium_mg="9000"
        ),
    )
    for goal in GoalType:
        for item in (best, worst):
            first = score_item(item, fx.prefs(goal=goal))
            second = score_item(item, fx.prefs(goal=goal))
            assert first == second
            assert Decimal("0") <= first.total_score <= Decimal("100")
            assert Decimal("0") <= first.confidence <= Decimal("1")


def test_calorie_fit_target_and_range() -> None:
    # Plate target 1350 kcal -> per-item target 450 kcal.
    on_target = fx.make_item("on", nutrition=fx.make_nutrition(calories="450"))
    breakdown = score_item(on_target, fx.prefs(calorie_target=Decimal("1350")))
    fit = {c.component: c.score for c in breakdown.components}[ScoreComponent.CALORIE_FIT]
    assert fit == Decimal("1.0000")
    assert PositiveReason.WITHIN_CALORIE_TARGET in breakdown.positive_reasons

    over = fx.make_item("over", nutrition=fx.make_nutrition(calories="900"))
    over_breakdown = score_item(over, fx.prefs(calorie_target=Decimal("1350")))
    over_fit = {c.component: c.score for c in over_breakdown.components}[
        ScoreComponent.CALORIE_FIT
    ]
    assert over_fit == Decimal("0.0000")
    assert CautionReason.ABOVE_CALORIE_TARGET in over_breakdown.cautions

    # Plate range 1200-1500 -> per-item 400-500: 450 sits inside.
    ranged = score_item(
        on_target, fx.prefs(calorie_min=Decimal("1200"), calorie_max=Decimal("1500"))
    )
    ranged_fit = {c.component: c.score for c in ranged.components}[ScoreComponent.CALORIE_FIT]
    assert ranged_fit == Decimal("1.0000")


def test_no_calorie_target_omits_calorie_fit_component() -> None:
    breakdown = score_item(fx.make_item(), fx.prefs())
    assert ScoreComponent.CALORIE_FIT not in {c.component for c in breakdown.components}


def test_uncertain_availability_and_serving_reduce_confidence_with_cautions() -> None:
    uncertain = fx.make_item(
        availability=OfferingStatus.UNKNOWN,
        nutrition=fx.make_nutrition(serving_size=None, serving_unit=None),
    )
    # 0.90 (serving unknown) x 0.85 (availability unknown) = 0.765 -> 0.77
    assert compute_confidence(uncertain) == Decimal("0.77")
    breakdown = score_item(uncertain, fx.prefs())
    assert CautionReason.SERVING_SIZE_UNKNOWN in breakdown.cautions
    assert CautionReason.AVAILABILITY_UNCERTAIN in breakdown.cautions
