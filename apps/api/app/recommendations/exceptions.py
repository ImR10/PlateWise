"""Typed exceptions for the recommendation engine.

Malformed input produces an explicit, typed error rather than silent behavior
(contract-level validation is handled by Pydantic ``ValidationError``).
"""

from __future__ import annotations


class RecommendationError(Exception):
    """Base class for all recommendation-engine errors."""


class DuplicateItemIdError(RecommendationError):
    """Two input items share the same stable item id."""

    def __init__(self, item_id: str) -> None:
        super().__init__(f"duplicate recommendation item id: {item_id!r}")
        self.item_id = item_id
