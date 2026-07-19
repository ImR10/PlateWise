"""Recommendation-domain contracts (Pydantic v2 DTOs).

These contracts are the engine's only input/output surface. They are
deliberately standalone: not coupled to SQLAlchemy ORM models, FastAPI, or the
(unfinished) Read API response schemas. A thin adapter added in a later
milestone will map Read API data onto :class:`RecommendationItem`.

Conventions shared with the import pipeline (`app/imports/contracts.py`):
frozen models with ``extra="forbid"``, all numeric quantities ``Decimal`` with
bounded, non-finite-rejecting annotated types, and missing values represented
as ``None`` — never zero.

Safety defaults are conservative: allergen and dietary-tag metadata is treated
as *incomplete* unless the adapter explicitly asserts completeness, and the
absence of a declaration is never interpreted as "allergen free".
"""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.db.enums import (
    AllergenDeclarationType,
    CalculationStatus,
    NutritionProvenance,
    NutritionReviewStatus,
    OfferingStatus,
    ProvenanceSourceType,
)
from app.imports.contracts import (
    MAX_DESCRIPTION_LENGTH,
    MAX_NAME_LENGTH,
    NutrientValues,
    ServingDecimal,
)
from app.imports.normalizers import normalize_name
from app.recommendations.enums import (
    CautionReason,
    ExclusionReason,
    GoalType,
    PositiveReason,
    ResultWarning,
    SafetyMode,
    ScoreComponent,
)

MAX_ITEM_ID_LENGTH = 255
MAX_ALLERGEN_NAME_LENGTH = 100
MAX_DIETARY_TAG_LENGTH = 100
MAX_ITEM_ALLERGENS = 100
MAX_ITEM_DIETARY_TAGS = 100
MAX_PREFERENCE_LIST_LENGTH = 100
MAX_RESULTS_LIMIT = 50
DEFAULT_MAX_RESULTS = 10

#: A strictly positive nutrient target (a target of zero is meaningless).
TargetDecimal = Annotated[
    Decimal, Field(gt=0, le=Decimal("99999999.99"), allow_inf_nan=False)
]
#: A bounded 0-1 confidence value.
ConfidenceDecimal = Annotated[Decimal, Field(ge=0, le=1, allow_inf_nan=False)]
#: A bounded 0-100 total score.
ScoreDecimal = Annotated[Decimal, Field(ge=0, le=100, allow_inf_nan=False)]


class _Contract(BaseModel):
    """Base config: strict-ish, immutable, forbids unknown fields."""

    model_config = ConfigDict(extra="forbid", frozen=True)


# ---------------------------------------------------------------------------
# Input contracts
# ---------------------------------------------------------------------------


class RecommendationNutrition(_Contract):
    """Nutrition for one item, with provenance and completeness metadata.

    Mirrors the semantics of the ``nutrition_facts`` model: any nutrient may be
    ``None`` (unknown) and is never coerced to zero; ``is_complete=False``
    calculated nutrition must never be presented as authoritative.
    """

    serving_size: ServingDecimal | None = None
    serving_unit: str | None = Field(default=None, max_length=50)
    nutrients: NutrientValues = Field(default_factory=NutrientValues)
    provenance: NutritionProvenance | None = None
    is_complete: bool = True
    review_status: NutritionReviewStatus = NutritionReviewStatus.NOT_REQUIRED
    calculation_status: CalculationStatus | None = None


class AllergenInfo(_Contract):
    """One allergen declaration. Absence of a declaration never means safe."""

    name: str = Field(min_length=1, max_length=MAX_ALLERGEN_NAME_LENGTH)
    declaration: AllergenDeclarationType = AllergenDeclarationType.CONTAINS

    @field_validator("name")
    @classmethod
    def _normalize(cls, value: str) -> str:
        normalized = normalize_name(value)
        if not normalized:
            raise ValueError("allergen name must not be blank")
        return normalized


class DietaryTagInfo(_Contract):
    """One dietary tag with provenance and optional 0-1 confidence."""

    name: str = Field(min_length=1, max_length=MAX_DIETARY_TAG_LENGTH)
    source_type: ProvenanceSourceType = ProvenanceSourceType.OFFICIAL
    confidence: ConfidenceDecimal | None = None

    @field_validator("name")
    @classmethod
    def _normalize(cls, value: str) -> str:
        normalized = normalize_name(value)
        if not normalized:
            raise ValueError("dietary tag name must not be blank")
        return normalized


class RecommendationItem(_Contract):
    """A normalized, source-neutral menu item offered to the engine.

    ``allergen_data_complete`` / ``dietary_tag_data_complete`` default to
    ``False``: an adapter must explicitly assert that the declared lists are
    exhaustive before the engine treats undeclared allergens/tags as absent.
    """

    item_id: str = Field(min_length=1, max_length=MAX_ITEM_ID_LENGTH)
    name: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)
    description: str | None = Field(default=None, max_length=MAX_DESCRIPTION_LENGTH)

    nutrition: RecommendationNutrition | None = None

    allergens: tuple[AllergenInfo, ...] = Field(default=(), max_length=MAX_ITEM_ALLERGENS)
    #: True only when the allergen declarations are known to be exhaustive.
    allergen_data_complete: bool = False

    dietary_tags: tuple[DietaryTagInfo, ...] = Field(
        default=(), max_length=MAX_ITEM_DIETARY_TAGS
    )
    #: True only when the dietary tags are known to be exhaustive.
    dietary_tag_data_complete: bool = False

    #: Official availability as published by the source (never inferred).
    availability: OfferingStatus = OfferingStatus.UNKNOWN

    #: Optional display context; never used for filtering or scoring.
    station_name: str | None = Field(default=None, max_length=MAX_NAME_LENGTH)
    venue_name: str | None = Field(default=None, max_length=MAX_NAME_LENGTH)

    @property
    def normalized_name(self) -> str:
        return normalize_name(self.name)


def _normalized_name_tuple(values: tuple[str, ...]) -> tuple[str, ...]:
    """Normalize, deduplicate, and sort a tuple of user-supplied names."""
    normalized = {normalize_name(value) for value in values}
    normalized.discard("")
    return tuple(sorted(normalized))


class UserPreferences(_Contract):
    """Explicit MVP contract for user intent. No free-form interpretation."""

    goal: GoalType = GoalType.BALANCED
    safety_mode: SafetyMode = SafetyMode.STRICT

    calorie_target: TargetDecimal | None = None
    calorie_min: TargetDecimal | None = None
    calorie_max: TargetDecimal | None = None
    protein_target_g: TargetDecimal | None = None

    excluded_allergens: tuple[str, ...] = Field(
        default=(), max_length=MAX_PREFERENCE_LIST_LENGTH
    )
    required_dietary_tags: tuple[str, ...] = Field(
        default=(), max_length=MAX_PREFERENCE_LIST_LENGTH
    )
    excluded_dietary_tags: tuple[str, ...] = Field(
        default=(), max_length=MAX_PREFERENCE_LIST_LENGTH
    )
    disliked_item_ids: tuple[str, ...] = Field(
        default=(), max_length=MAX_PREFERENCE_LIST_LENGTH
    )
    disliked_item_names: tuple[str, ...] = Field(
        default=(), max_length=MAX_PREFERENCE_LIST_LENGTH
    )

    max_results: int = Field(default=DEFAULT_MAX_RESULTS, ge=1, le=MAX_RESULTS_LIMIT)
    #: Opt-in basic plate assembly (see ``app/recommendations/plates.py``).
    assemble_plate: bool = False

    @field_validator(
        "excluded_allergens",
        "required_dietary_tags",
        "excluded_dietary_tags",
        "disliked_item_names",
    )
    @classmethod
    def _normalize_names(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _normalized_name_tuple(values)

    @field_validator("disliked_item_ids")
    @classmethod
    def _dedupe_ids(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(set(values)))

    @model_validator(mode="after")
    def _validate_ranges(self) -> UserPreferences:
        if (
            self.calorie_min is not None
            and self.calorie_max is not None
            and self.calorie_min > self.calorie_max
        ):
            raise ValueError("calorie_min must not exceed calorie_max")
        overlap = set(self.required_dietary_tags) & set(self.excluded_dietary_tags)
        if overlap:
            raise ValueError(
                f"dietary tags cannot be both required and excluded: {sorted(overlap)}"
            )
        return self


# ---------------------------------------------------------------------------
# Result contracts
# ---------------------------------------------------------------------------


class ComponentScore(_Contract):
    """One scored dimension: bounded score, its weight, and identity."""

    component: ScoreComponent
    weight: ConfidenceDecimal
    score: ConfidenceDecimal


class ScoreBreakdown(_Contract):
    """Transparent scoring output for one eligible item.

    ``components`` contains only the dimensions that were computable for this
    item; missing nutrients never contribute a zero score.
    """

    total_score: ScoreDecimal
    confidence: ConfidenceDecimal
    components: tuple[ComponentScore, ...]
    positive_reasons: tuple[PositiveReason, ...] = ()
    cautions: tuple[CautionReason, ...] = ()


class ScoredRecommendation(_Contract):
    """One ranked recommendation with its full explanation."""

    rank: int = Field(ge=1)
    item_id: str = Field(min_length=1, max_length=MAX_ITEM_ID_LENGTH)
    name: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)
    total_score: ScoreDecimal
    confidence: ConfidenceDecimal
    components: tuple[ComponentScore, ...]
    positive_reasons: tuple[PositiveReason, ...] = ()
    cautions: tuple[CautionReason, ...] = ()
    positive_explanations: tuple[str, ...] = ()
    caution_explanations: tuple[str, ...] = ()


class ExcludedItem(_Contract):
    """An item removed by hard filters, with machine-readable reasons."""

    item_id: str = Field(min_length=1, max_length=MAX_ITEM_ID_LENGTH)
    name: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)
    reasons: tuple[ExclusionReason, ...] = Field(min_length=1)
    explanations: tuple[str, ...] = Field(min_length=1)


class PlateSuggestion(_Contract):
    """A small deterministic combination of ranked items (optional feature).

    ``totals`` sums one serving of each selected item; a nutrient total is
    ``None`` whenever any selected item's value is unknown (never zero-filled).
    """

    item_ids: tuple[str, ...] = Field(min_length=1)
    item_names: tuple[str, ...] = Field(min_length=1)
    totals: NutrientValues
    warnings: tuple[ResultWarning, ...] = ()
    explanation: str


class InputSummary(_Contract):
    """Shape-only summary of the request (no preference values echoed)."""

    total_items: int = Field(ge=0)
    eligible_count: int = Field(ge=0)
    excluded_count: int = Field(ge=0)
    returned_count: int = Field(ge=0)
    goal: GoalType
    safety_mode: SafetyMode
    max_results: int = Field(ge=1, le=MAX_RESULTS_LIMIT)
    has_calorie_target: bool
    has_calorie_range: bool
    has_protein_target: bool
    excluded_allergen_count: int = Field(ge=0)
    required_dietary_tag_count: int = Field(ge=0)
    excluded_dietary_tag_count: int = Field(ge=0)
    disliked_item_count: int = Field(ge=0)


class RecommendationResult(_Contract):
    """Complete engine output, suitable for future API serialization."""

    recommendations: tuple[ScoredRecommendation, ...]
    excluded: tuple[ExcludedItem, ...]
    warnings: tuple[ResultWarning, ...] = ()
    warning_explanations: tuple[str, ...] = ()
    summary: InputSummary
    result_count: int = Field(ge=0)
    scoring_policy_version: str
    plate: PlateSuggestion | None = None
