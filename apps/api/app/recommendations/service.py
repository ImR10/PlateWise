"""Recommendation orchestration.

``recommend`` is the engine's single entry point: hard filters, then scoring,
then deterministic ranking, then the structured result. Pure domain logic —
no database, network, or FastAPI dependencies; repeated calls with the same
input produce the same output.

Deterministic ordering: total score descending, then data confidence
descending, then normalized name ascending, then item id ascending.

Observability: one structured completion event per run (counts, goal, mode,
duration, policy version). Preference payloads, item payloads, and full
results are intentionally never logged.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from time import perf_counter

from app.recommendations import explanations
from app.recommendations.contracts import (
    ExcludedItem,
    InputSummary,
    RecommendationItem,
    RecommendationResult,
    ScoredRecommendation,
    UserPreferences,
)
from app.recommendations.enums import CautionReason, ExclusionReason, ResultWarning
from app.recommendations.exceptions import DuplicateItemIdError
from app.recommendations.filters import evaluate_item
from app.recommendations.plates import assemble_plate
from app.recommendations.scoring import SCORING_POLICY_VERSION, score_item

logger = logging.getLogger(__name__)

#: Exclusion reasons that reflect unknown data rather than a confirmed conflict.
_UNKNOWN_DATA_REASONS = frozenset(
    {ExclusionReason.UNKNOWN_ALLERGEN_STATUS, ExclusionReason.UNKNOWN_DIETARY_STATUS}
)


def _check_unique_ids(items: Sequence[RecommendationItem]) -> None:
    seen: set[str] = set()
    for item in items:
        if item.item_id in seen:
            raise DuplicateItemIdError(item.item_id)
        seen.add(item.item_id)


def ranking_sort_key(
    pair: tuple[ScoredRecommendation, RecommendationItem],
) -> tuple[object, ...]:
    """Deterministic ranking order (see module docstring)."""
    rec, item = pair
    return (-rec.total_score, -rec.confidence, item.normalized_name, rec.item_id)


def _merge_cautions(
    filter_cautions: tuple[CautionReason, ...],
    scoring_cautions: tuple[CautionReason, ...],
) -> tuple[CautionReason, ...]:
    present = set(filter_cautions) | set(scoring_cautions)
    return tuple(caution for caution in CautionReason if caution in present)


def recommend(
    items: Sequence[RecommendationItem], preferences: UserPreferences
) -> RecommendationResult:
    """Produce ranked recommendations and explained exclusions for ``items``."""
    started = perf_counter()
    _check_unique_ids(items)

    excluded: list[ExcludedItem] = []
    scored: list[tuple[ScoredRecommendation, RecommendationItem]] = []

    for item in items:
        decision = evaluate_item(item, preferences)
        if not decision.eligible:
            excluded.append(
                ExcludedItem(
                    item_id=item.item_id,
                    name=item.name,
                    reasons=decision.reasons,
                    explanations=explanations.explain_exclusions(decision.reasons),
                )
            )
            continue

        breakdown = score_item(item, preferences)
        cautions = _merge_cautions(decision.cautions, breakdown.cautions)
        scored.append(
            (
                ScoredRecommendation(
                    rank=1,  # provisional; assigned after sorting
                    item_id=item.item_id,
                    name=item.name,
                    total_score=breakdown.total_score,
                    confidence=breakdown.confidence,
                    components=breakdown.components,
                    positive_reasons=breakdown.positive_reasons,
                    cautions=cautions,
                    positive_explanations=explanations.explain_positives(
                        breakdown.positive_reasons
                    ),
                    caution_explanations=explanations.explain_cautions(cautions),
                ),
                item,
            )
        )

    scored.sort(key=ranking_sort_key)
    ranked = [
        (rec.model_copy(update={"rank": position}), item)
        for position, (rec, item) in enumerate(scored, start=1)
    ]
    returned = tuple(rec for rec, _ in ranked[: preferences.max_results])

    warnings: list[ResultWarning] = []
    if not ranked:
        warnings.append(ResultWarning.NO_ELIGIBLE_ITEMS)
    if any(set(entry.reasons) & _UNKNOWN_DATA_REASONS for entry in excluded):
        warnings.append(ResultWarning.ITEMS_EXCLUDED_UNKNOWN_SAFETY_DATA)

    plate = None
    if preferences.assemble_plate and ranked:
        plate = assemble_plate(ranked, preferences)
        if plate is None:
            warnings.append(ResultWarning.PLATE_NOT_ASSEMBLED)

    ordered_warnings = tuple(w for w in ResultWarning if w in set(warnings))
    summary = InputSummary(
        total_items=len(items),
        eligible_count=len(ranked),
        excluded_count=len(excluded),
        returned_count=len(returned),
        goal=preferences.goal,
        safety_mode=preferences.safety_mode,
        max_results=preferences.max_results,
        has_calorie_target=preferences.calorie_target is not None,
        has_calorie_range=(
            preferences.calorie_min is not None or preferences.calorie_max is not None
        ),
        has_protein_target=preferences.protein_target_g is not None,
        excluded_allergen_count=len(preferences.excluded_allergens),
        required_dietary_tag_count=len(preferences.required_dietary_tags),
        excluded_dietary_tag_count=len(preferences.excluded_dietary_tags),
        disliked_item_count=(
            len(preferences.disliked_item_ids) + len(preferences.disliked_item_names)
        ),
    )

    duration_ms = round((perf_counter() - started) * 1000, 3)
    logger.info(
        "recommendation_run_completed",
        extra={
            "goal": preferences.goal.value,
            "safety_mode": preferences.safety_mode.value,
            "input_item_count": len(items),
            "eligible_count": len(ranked),
            "excluded_count": len(excluded),
            "returned_count": len(returned),
            "plate_assembled": plate is not None,
            "scoring_policy_version": SCORING_POLICY_VERSION,
            "duration_ms": duration_ms,
        },
    )

    return RecommendationResult(
        recommendations=returned,
        excluded=tuple(excluded),
        warnings=ordered_warnings,
        warning_explanations=explanations.explain_warnings(ordered_warnings),
        summary=summary,
        result_count=len(returned),
        scoring_policy_version=SCORING_POLICY_VERSION,
        plate=plate,
    )
