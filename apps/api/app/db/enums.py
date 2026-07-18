"""Enumerated value sets used across the PlateWise schema.

Each enum is rendered as a native PostgreSQL ``ENUM`` type. Using database
enums gives us validation at the storage layer (an invalid value is rejected
by the database, not just the application) while remaining readable in SQL.

The string values -- not the Python member names -- are what gets stored, so
models declare their columns with ``values_callable`` pointing at
:func:`enum_values`.
"""

from __future__ import annotations

import enum
from collections.abc import Sequence
from enum import StrEnum

from sqlalchemy import Enum as SAEnum

# ``StrEnum`` members are ``str`` subclasses whose value is stored, which keeps
# fixtures, API payloads, and assertions ergonomic (``member == "value"``).


def enum_values(enum_cls: type[enum.Enum]) -> Sequence[str]:
    """Return the stored string values for a SQLAlchemy ``Enum(values_callable=...)``."""
    return [member.value for member in enum_cls]


def pg_enum(enum_cls: type[enum.Enum], name: str) -> SAEnum:
    """Build a native PostgreSQL ENUM column type for ``enum_cls``.

    Stores the enum *values* (lowercase strings) rather than the Python member
    names, and gives the database type an explicit, stable ``name``.
    """
    return SAEnum(enum_cls, name=name, values_callable=enum_values, native_enum=True)


class InstitutionType(StrEnum):
    """Category of organization that owns a catalog and venue hierarchy."""

    UNIVERSITY = "university"
    HOSPITAL = "hospital"
    CORPORATE_CAMPUS = "corporate_campus"
    SENIOR_LIVING = "senior_living"
    GOVERNMENT = "government"
    OTHER = "other"


class VenueType(StrEnum):
    """Category of physical place where food is served."""

    DINING_HALL = "dining_hall"
    CAFETERIA = "cafeteria"
    CAFE = "cafe"
    FOOD_COURT = "food_court"
    RESTAURANT = "restaurant"
    OTHER = "other"


class ProvenanceSourceType(StrEnum):
    """Where a piece of derived catalog metadata came from.

    Shared by aliases, allergen declarations, and dietary tags to describe how
    trustworthy the association is.
    """

    OFFICIAL = "official"
    IMPORTED = "imported"
    USER_SUGGESTED = "user_suggested"
    MANUALLY_VERIFIED = "manually_verified"


class NutritionSourceType(StrEnum):
    """Origin of a nutrition record."""

    OFFICIAL = "official"
    RECIPE_CALCULATED = "recipe_calculated"
    USDA_MATCH = "usda_match"
    MANUAL = "manual"
    ESTIMATED = "estimated"


class AllergenDeclarationType(StrEnum):
    """Strength of an allergen declaration for a menu item.

    The absence of a declaration must never be interpreted as "allergen free".
    """

    CONTAINS = "contains"
    MAY_CONTAIN = "may_contain"
    FACILITY_WARNING = "facility_warning"
    UNKNOWN = "unknown"


class MealPeriod(StrEnum):
    """Named service window an offering belongs to."""

    BREAKFAST = "breakfast"
    BRUNCH = "brunch"
    LUNCH = "lunch"
    DINNER = "dinner"
    LATE_NIGHT = "late_night"
    ALL_DAY = "all_day"
    OTHER = "other"


class OfferingStatus(StrEnum):
    """Official availability status of an offering as published by the source.

    Community reports never overwrite this value; effective availability is
    computed separately from reports.
    """

    SCHEDULED = "scheduled"
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


class ReportType(StrEnum):
    """Kind of community observation about a specific offering."""

    SOLD_OUT = "sold_out"
    NOT_PRESENT = "not_present"
    REPLACEMENT = "replacement"
    AVAILABLE_NOW = "available_now"
    BACK_IN_STOCK = "back_in_stock"
    WRONG_STATION = "wrong_station"
    WRONG_ITEM = "wrong_item"
    WRONG_NUTRITION = "wrong_nutrition"
    STAFF_CONFIRMED = "staff_confirmed"
    OTHER = "other"


class ModerationStatus(StrEnum):
    """Moderation lifecycle state of a community report."""

    ACTIVE = "active"
    RETRACTED = "retracted"
    FLAGGED = "flagged"
    REJECTED = "rejected"
    CONFIRMED = "confirmed"


class SuggestionStatus(StrEnum):
    """Lifecycle state of a proposed (not yet catalogued) menu item."""

    PENDING = "pending"
    MATCHED = "matched"
    APPROVED = "approved"
    REJECTED = "rejected"
    DUPLICATE = "duplicate"


class ImportSourceType(StrEnum):
    """Origin of an ingested payload (also used for offering provenance)."""

    FIXTURE = "fixture"
    JSON = "json"
    CSV = "csv"
    FOODPRO_EXPORT = "foodpro_export"
    NUTRISLICE_EXPORT = "nutrislice_export"
    MANUAL = "manual"
    OTHER = "other"


class ImportStatus(StrEnum):
    """Lifecycle state of a data import run."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    COMPLETED_WITH_ERRORS = "completed_with_errors"
    FAILED = "failed"
