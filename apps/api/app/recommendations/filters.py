"""Hard eligibility filtering.

Filters run before any scoring. Every excluded item carries one or more
machine-readable :class:`~app.recommendations.enums.ExclusionReason` codes —
nothing is silently discarded.

Safety rules (see docs/mvp-sequence.md and the catalog model docstrings):

* Absence of an allergen declaration is never interpreted as allergen-free.
* Absence of a dietary tag is never interpreted as certainty either way.
* Missing nutrition stays unknown; it is never treated as zero.
* In ``strict`` mode (the default), unknown safety metadata excludes an item
  whenever the user's preferences depend on that metadata. In ``permissive``
  mode the item stays eligible but carries explicit cautions.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.db.enums import AllergenDeclarationType, OfferingStatus, ProvenanceSourceType
from app.imports.enums import NUTRIENT_FIELDS
from app.recommendations.contracts import RecommendationItem, UserPreferences
from app.recommendations.enums import CautionReason, ExclusionReason, GoalType, SafetyMode

#: Explicit, documented tag equivalence: a requirement for ``vegetarian`` is
#: satisfied by a ``vegan`` tag (a vegan item is by definition vegetarian).
#: This is a fixed lookup table, not keyword matching.
REQUIRED_TAG_SATISFIED_BY: dict[str, frozenset[str]] = {
    "vegetarian": frozenset({"vegetarian", "vegan"}),
}

#: Dietary-tag provenance values trusted without a caution.
VERIFIED_TAG_SOURCES = frozenset(
    {ProvenanceSourceType.OFFICIAL, ProvenanceSourceType.MANUALLY_VERIFIED}
)

#: Official statuses that mean the item is confirmed not being served.
CONFIRMED_UNAVAILABLE = frozenset({OfferingStatus.UNAVAILABLE, OfferingStatus.CANCELLED})

#: Allergen declarations that assert possible (not confirmed) presence.
POSSIBLE_PRESENCE = frozenset(
    {AllergenDeclarationType.MAY_CONTAIN, AllergenDeclarationType.FACILITY_WARNING}
)


@dataclass(frozen=True)
class EligibilityDecision:
    """Outcome of hard filtering for one item."""

    reasons: tuple[ExclusionReason, ...]
    cautions: tuple[CautionReason, ...]

    @property
    def eligible(self) -> bool:
        return not self.reasons


def required_tags_for(preferences: UserPreferences) -> tuple[str, ...]:
    """The user's required tags plus tags implied by the selected goal."""
    required = set(preferences.required_dietary_tags)
    if preferences.goal is GoalType.VEGETARIAN:
        required.add("vegetarian")
    return tuple(sorted(required))


def _allergen_reasons(
    item: RecommendationItem, preferences: UserPreferences
) -> tuple[list[ExclusionReason], list[CautionReason]]:
    if not preferences.excluded_allergens:
        return [], []

    strict = preferences.safety_mode is SafetyMode.STRICT
    reasons: list[ExclusionReason] = []
    cautions: list[CautionReason] = []

    declarations: dict[str, set[AllergenDeclarationType]] = {}
    for info in item.allergens:
        declarations.setdefault(info.name, set()).add(info.declaration)

    conflict = False
    unknown_status = False
    for allergen in preferences.excluded_allergens:
        declared = declarations.get(allergen, set())
        if AllergenDeclarationType.CONTAINS in declared:
            conflict = True
        elif declared & POSSIBLE_PRESENCE:
            # Possible presence: strict mode treats it as a conflict; permissive
            # mode keeps the item but never claims it is safe.
            if strict:
                conflict = True
            else:
                cautions.append(CautionReason.MAY_CONTAIN_EXCLUDED_ALLERGEN)
        elif AllergenDeclarationType.UNKNOWN in declared or not item.allergen_data_complete:
            # No usable declaration: status for this allergen is unknown.
            unknown_status = True

    if conflict:
        reasons.append(ExclusionReason.ALLERGEN_CONFLICT)
    if unknown_status:
        if strict:
            reasons.append(ExclusionReason.UNKNOWN_ALLERGEN_STATUS)
        else:
            cautions.append(CautionReason.ALLERGEN_DATA_INCOMPLETE)
    return reasons, cautions


def _dietary_reasons(
    item: RecommendationItem, preferences: UserPreferences
) -> tuple[list[ExclusionReason], list[CautionReason]]:
    strict = preferences.safety_mode is SafetyMode.STRICT
    reasons: list[ExclusionReason] = []
    cautions: list[CautionReason] = []

    tags_by_name = {tag.name: tag for tag in item.dietary_tags}

    conflict = False
    unknown_status = False
    for required in required_tags_for(preferences):
        satisfying = REQUIRED_TAG_SATISFIED_BY.get(required, frozenset({required}))
        matches = [tags_by_name[name] for name in sorted(satisfying) if name in tags_by_name]
        if matches:
            if all(tag.source_type not in VERIFIED_TAG_SOURCES for tag in matches):
                cautions.append(CautionReason.UNVERIFIED_DIETARY_TAG)
        elif item.dietary_tag_data_complete:
            # The tag list is exhaustive and the required tag is absent.
            conflict = True
        else:
            unknown_status = True

    # A present excluded tag is a positive assertion: conflict in both modes.
    if any(tag in tags_by_name for tag in preferences.excluded_dietary_tags):
        conflict = True

    if conflict:
        reasons.append(ExclusionReason.DIETARY_CONFLICT)
    if unknown_status:
        if strict:
            reasons.append(ExclusionReason.UNKNOWN_DIETARY_STATUS)
        else:
            cautions.append(CautionReason.DIETARY_DATA_INCOMPLETE)
    return reasons, cautions


def _nutrition_reasons(
    item: RecommendationItem, preferences: UserPreferences
) -> list[ExclusionReason]:
    strict = preferences.safety_mode is SafetyMode.STRICT
    nutrition = item.nutrition
    if nutrition is None:
        return [ExclusionReason.INSUFFICIENT_NUTRITION_DATA]

    values = nutrition.nutrients
    if all(getattr(values, field) is None for field in NUTRIENT_FIELDS):
        return [ExclusionReason.INSUFFICIENT_NUTRITION_DATA]

    if strict:
        # Strict mode requires the anchor nutrient and refuses nutrition that
        # the catalog itself marks as not authoritative (incomplete).
        if values.calories is None or not nutrition.is_complete:
            return [ExclusionReason.INSUFFICIENT_NUTRITION_DATA]
    return []


def evaluate_item(
    item: RecommendationItem, preferences: UserPreferences
) -> EligibilityDecision:
    """Apply every hard filter to one item.

    Returns all applicable exclusion reasons (not just the first) plus any
    cautions that must accompany the item if it remains eligible.
    """
    reasons: list[ExclusionReason] = []
    cautions: list[CautionReason] = []

    if (
        item.item_id in preferences.disliked_item_ids
        or item.normalized_name in preferences.disliked_item_names
    ):
        reasons.append(ExclusionReason.USER_EXCLUDED)

    if item.availability in CONFIRMED_UNAVAILABLE:
        reasons.append(ExclusionReason.UNAVAILABLE)

    allergen_reasons, allergen_cautions = _allergen_reasons(item, preferences)
    reasons.extend(allergen_reasons)
    cautions.extend(allergen_cautions)

    dietary_reasons, dietary_cautions = _dietary_reasons(item, preferences)
    reasons.extend(dietary_reasons)
    cautions.extend(dietary_cautions)

    reasons.extend(_nutrition_reasons(item, preferences))

    # Deduplicate while keeping deterministic, definition-order output.
    ordered_reasons = tuple(r for r in ExclusionReason if r in set(reasons))
    ordered_cautions = tuple(c for c in CautionReason if c in set(cautions))
    return EligibilityDecision(reasons=ordered_reasons, cautions=ordered_cautions)
