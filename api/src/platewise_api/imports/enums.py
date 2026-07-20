"""Import-pipeline enums that are not persisted as database types."""

from __future__ import annotations

from enum import StrEnum


class RecordClassification(StrEnum):
    """Classification of an incoming menu-item record before persistence."""

    NUTRITION_READY = "nutrition_ready"
    RECIPE_READY = "recipe_ready"
    INCOMPLETE = "incomplete"
    INVALID = "invalid"
