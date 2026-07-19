"""Explanation coverage and consistency tests (no database)."""

from __future__ import annotations

from decimal import Decimal

import recommendation_fixtures as fx

from app.recommendations.enums import (
    CautionReason,
    ExclusionReason,
    PositiveReason,
    ResultWarning,
    SafetyMode,
    ScoreComponent,
)
from app.recommendations.explanations import (
    CAUTION_TEXT,
    EXCLUSION_TEXT,
    POSITIVE_TEXT,
    WARNING_TEXT,
    explain_cautions,
    explain_exclusions,
    explain_positives,
)
from app.recommendations.scoring import score_item
from app.recommendations.service import recommend

#: Every positive reason is backed by exactly one score component.
REASON_COMPONENT: dict[PositiveReason, ScoreComponent] = {
    PositiveReason.HIGH_PROTEIN: ScoreComponent.PROTEIN_ADEQUACY,
    PositiveReason.PROTEIN_DENSE: ScoreComponent.PROTEIN_DENSITY,
    PositiveReason.WITHIN_CALORIE_TARGET: ScoreComponent.CALORIE_FIT,
    PositiveReason.LOW_CALORIE: ScoreComponent.CALORIE_MODERATION,
    PositiveReason.HIGH_FIBER: ScoreComponent.FIBER_ADEQUACY,
    PositiveReason.LOW_SODIUM: ScoreComponent.SODIUM_MODERATION,
}


def test_every_code_has_an_explanation() -> None:
    assert set(POSITIVE_TEXT) == set(PositiveReason)
    assert set(CAUTION_TEXT) == set(CautionReason)
    assert set(EXCLUSION_TEXT) == set(ExclusionReason)
    assert set(WARNING_TEXT) == set(ResultWarning)
    for mapping in (POSITIVE_TEXT, CAUTION_TEXT, EXCLUSION_TEXT, WARNING_TEXT):
        assert all(isinstance(text, str) and text for text in mapping.values())


def test_reason_codes_are_machine_readable_and_stable() -> None:
    assert ExclusionReason.ALLERGEN_CONFLICT.value == "ALLERGEN_CONFLICT"
    assert ExclusionReason.DIETARY_CONFLICT.value == "DIETARY_CONFLICT"
    assert ExclusionReason.UNAVAILABLE.value == "UNAVAILABLE"
    assert ExclusionReason.USER_EXCLUDED.value == "USER_EXCLUDED"
    assert ExclusionReason.UNKNOWN_ALLERGEN_STATUS.value == "UNKNOWN_ALLERGEN_STATUS"
    assert (
        ExclusionReason.INSUFFICIENT_NUTRITION_DATA.value == "INSUFFICIENT_NUTRITION_DATA"
    )


def test_human_readable_explanations_are_stable() -> None:
    reasons = (ExclusionReason.UNAVAILABLE, ExclusionReason.USER_EXCLUDED)
    assert explain_exclusions(reasons) == (
        "Not currently available according to the source.",
        "You asked to exclude this item.",
    )
    assert explain_positives((PositiveReason.HIGH_FIBER,)) == ("A good source of fiber.",)
    assert explain_cautions((CautionReason.SERVING_SIZE_UNKNOWN,)) == (
        "Serving size is unknown.",
    )


def test_cautions_present_for_uncertain_data() -> None:
    item = fx.make_item(
        nutrition=fx.make_nutrition(protein_g=None, serving_size=None, serving_unit=None)
    )
    result = recommend([item], fx.prefs(safety_mode=SafetyMode.PERMISSIVE))
    (rec,) = result.recommendations
    assert CautionReason.MISSING_NUTRIENTS in rec.cautions
    assert CautionReason.SERVING_SIZE_UNKNOWN in rec.cautions
    assert len(rec.caution_explanations) == len(rec.cautions)


def test_positive_reasons_match_actual_score_components() -> None:
    item = fx.make_item(
        nutrition=fx.make_nutrition(
            calories="450", protein_g="40", fiber_g="8", sodium_mg="150"
        )
    )
    breakdown = score_item(item, fx.prefs())
    components = {c.component: c.score for c in breakdown.components}
    assert breakdown.positive_reasons  # this item earns several
    for reason in breakdown.positive_reasons:
        component = REASON_COMPONENT[reason]
        assert component in components
        # A positive claim requires strong supporting component evidence
        # (0.70 is the lowest positive-reason threshold in the policy).
        assert components[component] >= Decimal("0.70")


def test_no_unsupported_safety_claims_in_uncertainty_text() -> None:
    uncertain_codes = [
        CAUTION_TEXT[CautionReason.MAY_CONTAIN_EXCLUDED_ALLERGEN],
        CAUTION_TEXT[CautionReason.ALLERGEN_DATA_INCOMPLETE],
        EXCLUSION_TEXT[ExclusionReason.UNKNOWN_ALLERGEN_STATUS],
        EXCLUSION_TEXT[ExclusionReason.UNKNOWN_DIETARY_STATUS],
        WARNING_TEXT[ResultWarning.ITEMS_EXCLUDED_UNKNOWN_SAFETY_DATA],
    ]
    for text in uncertain_codes:
        lowered = text.lower()
        assert any(
            marker in lowered
            for marker in ("unknown", "incomplete", "not confirmed", "may contain")
        )
        assert "guaranteed" not in lowered
        assert "allergen-free" not in lowered


def test_explanations_align_with_codes_in_results() -> None:
    items = [
        fx.make_item("good", "Good Bowl"),
        fx.make_item("gone", "Gone Bowl", availability="unavailable"),
    ]
    result = recommend(items, fx.prefs())
    for excluded in result.excluded:
        assert excluded.explanations == explain_exclusions(excluded.reasons)
    for rec in result.recommendations:
        assert rec.positive_explanations == explain_positives(rec.positive_reasons)
        assert rec.caution_explanations == explain_cautions(rec.cautions)
