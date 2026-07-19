"""Hard eligibility filtering tests (no database)."""

from __future__ import annotations

import recommendation_fixtures as fx

from app.db.enums import AllergenDeclarationType, OfferingStatus, ProvenanceSourceType
from app.recommendations.enums import CautionReason, ExclusionReason, GoalType, SafetyMode
from app.recommendations.filters import evaluate_item


def test_confirmed_allergen_conflict_excluded_in_both_modes() -> None:
    item = fx.make_item(
        allergens=(fx.allergen("peanut", AllergenDeclarationType.CONTAINS),),
        allergen_data_complete=True,
    )
    for mode in (SafetyMode.STRICT, SafetyMode.PERMISSIVE):
        decision = evaluate_item(
            item, fx.prefs(excluded_allergens=("peanut",), safety_mode=mode)
        )
        assert not decision.eligible
        assert ExclusionReason.ALLERGEN_CONFLICT in decision.reasons


def test_unknown_allergen_status_strict_mode_excludes() -> None:
    # No declarations at all, and the list is not asserted complete.
    item = fx.make_item(allergen_data_complete=False)
    decision = evaluate_item(item, fx.prefs(excluded_allergens=("peanut",)))
    assert decision.reasons == (ExclusionReason.UNKNOWN_ALLERGEN_STATUS,)


def test_unknown_allergen_status_permissive_mode_keeps_with_caution() -> None:
    item = fx.make_item(allergen_data_complete=False)
    decision = evaluate_item(
        item,
        fx.prefs(excluded_allergens=("peanut",), safety_mode=SafetyMode.PERMISSIVE),
    )
    assert decision.eligible
    assert CautionReason.ALLERGEN_DATA_INCOMPLETE in decision.cautions


def test_complete_allergen_data_without_declaration_is_eligible_in_strict() -> None:
    item = fx.make_item(allergen_data_complete=True)
    decision = evaluate_item(item, fx.prefs(excluded_allergens=("peanut",)))
    assert decision.eligible


def test_may_contain_strict_excludes_permissive_cautions() -> None:
    item = fx.make_item(
        allergens=(fx.allergen("milk", AllergenDeclarationType.MAY_CONTAIN),),
        allergen_data_complete=True,
    )
    strict = evaluate_item(item, fx.prefs(excluded_allergens=("milk",)))
    assert strict.reasons == (ExclusionReason.ALLERGEN_CONFLICT,)

    permissive = evaluate_item(
        item, fx.prefs(excluded_allergens=("milk",), safety_mode=SafetyMode.PERMISSIVE)
    )
    assert permissive.eligible
    assert CautionReason.MAY_CONTAIN_EXCLUDED_ALLERGEN in permissive.cautions


def test_no_excluded_allergens_means_no_allergen_filtering() -> None:
    item = fx.make_item(allergen_data_complete=False)
    assert evaluate_item(item, fx.prefs()).eligible


def test_vegetarian_goal_conflict_excluded() -> None:
    meat = fx.make_item(dietary_tag_data_complete=True)  # complete tags, none listed
    decision = evaluate_item(meat, fx.prefs(goal=GoalType.VEGETARIAN))
    assert ExclusionReason.DIETARY_CONFLICT in decision.reasons


def test_vegetarian_goal_satisfied_by_vegetarian_or_vegan_tag() -> None:
    for tag_name in ("vegetarian", "vegan"):
        item = fx.make_item(dietary_tags=(fx.tag(tag_name),))
        assert evaluate_item(item, fx.prefs(goal=GoalType.VEGETARIAN)).eligible


def test_required_tag_unknown_strict_excludes_permissive_cautions() -> None:
    item = fx.make_item(dietary_tag_data_complete=False)
    strict = evaluate_item(item, fx.prefs(required_dietary_tags=("vegan",)))
    assert strict.reasons == (ExclusionReason.UNKNOWN_DIETARY_STATUS,)

    permissive = evaluate_item(
        item,
        fx.prefs(required_dietary_tags=("vegan",), safety_mode=SafetyMode.PERMISSIVE),
    )
    assert permissive.eligible
    assert CautionReason.DIETARY_DATA_INCOMPLETE in permissive.cautions


def test_excluded_tag_present_is_conflict_even_with_incomplete_data() -> None:
    item = fx.make_item(dietary_tags=(fx.tag("spicy"),), dietary_tag_data_complete=False)
    for mode in (SafetyMode.STRICT, SafetyMode.PERMISSIVE):
        decision = evaluate_item(
            item, fx.prefs(excluded_dietary_tags=("spicy",), safety_mode=mode)
        )
        assert ExclusionReason.DIETARY_CONFLICT in decision.reasons


def test_unverified_required_tag_carries_caution() -> None:
    item = fx.make_item(
        dietary_tags=(fx.tag("vegan", source_type=ProvenanceSourceType.USER_SUGGESTED),)
    )
    decision = evaluate_item(item, fx.prefs(required_dietary_tags=("vegan",)))
    assert decision.eligible
    assert CautionReason.UNVERIFIED_DIETARY_TAG in decision.cautions


def test_unavailable_and_cancelled_excluded_unknown_is_not() -> None:
    for status in (OfferingStatus.UNAVAILABLE, OfferingStatus.CANCELLED):
        item = fx.make_item(availability=status)
        assert evaluate_item(item, fx.prefs()).reasons == (ExclusionReason.UNAVAILABLE,)
    unknown = fx.make_item(availability=OfferingStatus.UNKNOWN)
    assert evaluate_item(unknown, fx.prefs()).eligible


def test_user_excluded_by_id_and_by_name() -> None:
    item = fx.make_item("chicken-1", "Grilled Chicken")
    by_id = evaluate_item(item, fx.prefs(disliked_item_ids=("chicken-1",)))
    assert by_id.reasons == (ExclusionReason.USER_EXCLUDED,)
    by_name = evaluate_item(item, fx.prefs(disliked_item_names=("  grilled CHICKEN ",)))
    assert by_name.reasons == (ExclusionReason.USER_EXCLUDED,)


def test_missing_nutrition_excluded_with_reason() -> None:
    no_nutrition = fx.make_item(nutrition=None)
    all_none = fx.make_item(
        nutrition=fx.make_nutrition(
            calories=None,
            protein_g=None,
            carbohydrates_g=None,
            fat_g=None,
            saturated_fat_g=None,
            fiber_g=None,
            sugar_g=None,
            sodium_mg=None,
            cholesterol_mg=None,
        )
    )
    for item in (no_nutrition, all_none):
        decision = evaluate_item(item, fx.prefs())
        assert decision.reasons == (ExclusionReason.INSUFFICIENT_NUTRITION_DATA,)


def test_strict_requires_calories_permissive_does_not() -> None:
    item = fx.make_item(nutrition=fx.make_nutrition(calories=None))
    strict = evaluate_item(item, fx.prefs())
    assert strict.reasons == (ExclusionReason.INSUFFICIENT_NUTRITION_DATA,)
    permissive = evaluate_item(item, fx.prefs(safety_mode=SafetyMode.PERMISSIVE))
    assert permissive.eligible


def test_strict_rejects_incomplete_nutrition_permissive_keeps() -> None:
    item = fx.make_item(nutrition=fx.make_nutrition(is_complete=False))
    strict = evaluate_item(item, fx.prefs())
    assert strict.reasons == (ExclusionReason.INSUFFICIENT_NUTRITION_DATA,)
    permissive = evaluate_item(item, fx.prefs(safety_mode=SafetyMode.PERMISSIVE))
    assert permissive.eligible


def test_multiple_exclusion_reasons_are_all_reported() -> None:
    item = fx.make_item(
        "bad-1",
        "Peanut Stew",
        nutrition=None,
        allergens=(fx.allergen("peanut"),),
        allergen_data_complete=True,
        availability=OfferingStatus.CANCELLED,
    )
    decision = evaluate_item(
        item, fx.prefs(excluded_allergens=("peanut",), disliked_item_ids=("bad-1",))
    )
    assert set(decision.reasons) == {
        ExclusionReason.ALLERGEN_CONFLICT,
        ExclusionReason.UNAVAILABLE,
        ExclusionReason.USER_EXCLUDED,
        ExclusionReason.INSUFFICIENT_NUTRITION_DATA,
    }


def test_no_silent_exclusions() -> None:
    # Every ineligible decision must carry at least one reason.
    items = [
        fx.make_item("a", nutrition=None),
        fx.make_item("b", availability=OfferingStatus.UNAVAILABLE),
        fx.make_item("c"),
    ]
    for item in items:
        decision = evaluate_item(item, fx.prefs())
        assert decision.eligible or decision.reasons
