"""Deterministic ranking and result-shape tests (no database)."""

from __future__ import annotations

from decimal import Decimal

import recommendation_fixtures as fx

from platewise_api.recommendations.contracts import ScoredRecommendation
from platewise_api.recommendations.enums import ExclusionReason, ResultWarning
from platewise_api.recommendations.service import ranking_sort_key, recommend


def _rec(item_id: str, score: str, confidence: str) -> ScoredRecommendation:
    return ScoredRecommendation(
        rank=1,
        item_id=item_id,
        name=f"Item {item_id}",
        total_score=Decimal(score),
        confidence=Decimal(confidence),
        components=(),
    )


def test_repeated_calls_produce_identical_output() -> None:
    items = [
        fx.make_item("a", "Apple Salad"),
        fx.make_item("b", "Bean Bowl", nutrition=fx.make_nutrition(protein_g="12")),
        fx.make_item("c", "Chicken", nutrition=fx.make_nutrition(sodium_mg="1200")),
    ]
    preferences = fx.prefs()
    first = recommend(items, preferences)
    second = recommend(items, preferences)
    assert first == second
    # Input order does not affect the ranking order.
    shuffled = recommend(list(reversed(items)), preferences)
    assert [r.item_id for r in shuffled.recommendations] == [
        r.item_id for r in first.recommendations
    ]


def test_tie_breaking_is_score_confidence_name_then_id() -> None:
    pairs = [
        (_rec("z", "50", "0.90"), fx.make_item("z", "Beta")),
        (_rec("y", "50", "0.90"), fx.make_item("y", "Alpha")),
        (_rec("x", "50", "0.95"), fx.make_item("x", "Gamma")),
        (_rec("w", "60", "0.10"), fx.make_item("w", "Delta")),
    ]
    ordered = sorted(pairs, key=ranking_sort_key)
    assert [rec.item_id for rec, _ in ordered] == ["w", "x", "y", "z"]


def test_stable_ordering_with_duplicate_names() -> None:
    # Identical items (same name, same nutrition) differ only by id.
    items = [
        fx.make_item("id-2", "Tofu Bowl"),
        fx.make_item("id-1", "Tofu Bowl"),
        fx.make_item("id-3", "Tofu Bowl"),
    ]
    result = recommend(items, fx.prefs())
    assert [r.item_id for r in result.recommendations] == ["id-1", "id-2", "id-3"]
    assert [r.rank for r in result.recommendations] == [1, 2, 3]


def test_all_items_tied_order_by_name() -> None:
    items = [
        fx.make_item("1", "Cherry Cup"),
        fx.make_item("2", "Apple Cup"),
        fx.make_item("3", "Banana Cup"),
    ]
    result = recommend(items, fx.prefs())
    assert [r.name for r in result.recommendations] == [
        "Apple Cup",
        "Banana Cup",
        "Cherry Cup",
    ]
    scores = {r.total_score for r in result.recommendations}
    assert len(scores) == 1


def test_result_limit_enforced_excluded_not_truncated() -> None:
    items = [fx.make_item(f"i{n}", f"Item {n:02d}") for n in range(5)]
    items.append(fx.make_item("no-data", "Mystery", nutrition=None))
    result = recommend(items, fx.prefs(max_results=2))
    assert len(result.recommendations) == 2
    assert result.result_count == 2
    assert result.summary.eligible_count == 5
    assert len(result.excluded) == 1
    # The returned items are the top of the full ranking.
    assert [r.rank for r in result.recommendations] == [1, 2]


def test_no_eligible_items() -> None:
    items = [fx.make_item("a", nutrition=None)]
    result = recommend(items, fx.prefs())
    assert result.recommendations == ()
    assert result.result_count == 0
    assert ResultWarning.NO_ELIGIBLE_ITEMS in result.warnings
    assert len(result.warning_explanations) == len(result.warnings)


def test_one_eligible_item() -> None:
    result = recommend([fx.make_item()], fx.prefs())
    assert len(result.recommendations) == 1
    assert result.recommendations[0].rank == 1


def test_excluded_items_returned_separately_with_reasons() -> None:
    items = [
        fx.make_item("good", "Good Bowl"),
        fx.make_item("bad", "Bad Bowl", nutrition=None),
    ]
    result = recommend(items, fx.prefs())
    assert [r.item_id for r in result.recommendations] == ["good"]
    assert [e.item_id for e in result.excluded] == ["bad"]
    excluded = result.excluded[0]
    assert excluded.reasons == (ExclusionReason.INSUFFICIENT_NUTRITION_DATA,)
    assert len(excluded.explanations) == len(excluded.reasons)


def test_empty_input_is_valid() -> None:
    result = recommend([], fx.prefs())
    assert result.recommendations == ()
    assert result.excluded == ()
    assert result.summary.total_items == 0
    assert ResultWarning.NO_ELIGIBLE_ITEMS in result.warnings
