"""PlateWise recommendation foundation.

A standalone, deterministic, testable domain component. It accepts normalized
:class:`RecommendationItem` inputs plus :class:`UserPreferences` and produces a
:class:`RecommendationResult` with eligible/excluded items, transparent
scoring, and uncertainty warnings. No FastAPI, database, or Read API
dependencies; a thin adapter from the Read API is a later milestone.
See ``docs/recommendation-foundation-architecture.md``.
"""

from app.recommendations.contracts import (
    AllergenInfo,
    DietaryTagInfo,
    ExcludedItem,
    InputSummary,
    PlateSuggestion,
    RecommendationItem,
    RecommendationNutrition,
    RecommendationResult,
    ScoredRecommendation,
    UserPreferences,
)
from app.recommendations.enums import (
    CautionReason,
    ExclusionReason,
    GoalType,
    PositiveReason,
    ResultWarning,
    SafetyMode,
    ScoreComponent,
)
from app.recommendations.exceptions import DuplicateItemIdError, RecommendationError
from app.recommendations.scoring import SCORING_POLICY_VERSION
from app.recommendations.service import recommend

__all__ = [
    "AllergenInfo",
    "CautionReason",
    "DietaryTagInfo",
    "DuplicateItemIdError",
    "ExcludedItem",
    "ExclusionReason",
    "GoalType",
    "InputSummary",
    "PlateSuggestion",
    "PositiveReason",
    "RecommendationError",
    "RecommendationItem",
    "RecommendationNutrition",
    "RecommendationResult",
    "ResultWarning",
    "SCORING_POLICY_VERSION",
    "SafetyMode",
    "ScoreComponent",
    "ScoredRecommendation",
    "UserPreferences",
    "recommend",
]
