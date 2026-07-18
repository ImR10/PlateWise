"""Source-neutral import contracts (Pydantic v2 DTOs).

Source adapters convert provider-specific payloads (JSON/CSV/...) into these
DTOs before anything else in the pipeline runs. Nothing downstream --
classification, normalization, calculation, or persistence -- may depend on a
source's native structure.

All numeric quantities are ``Decimal`` (see :mod:`app.imports.decimal_utils`).
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.db.enums import InstitutionType, MealPeriod, VenueType


class _Contract(BaseModel):
    """Base config: strict-ish, immutable, forbids unknown fields."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class NutrientValues(_Contract):
    """The nutrients PlateWise tracks. Any nutrient may be ``None`` (unknown).

    A missing nutrient is ``None`` and is never coerced to zero.
    """

    calories: Decimal | None = None
    protein_g: Decimal | None = None
    carbohydrates_g: Decimal | None = None
    fat_g: Decimal | None = None
    saturated_fat_g: Decimal | None = None
    fiber_g: Decimal | None = None
    sugar_g: Decimal | None = None
    sodium_mg: Decimal | None = None
    cholesterol_mg: Decimal | None = None


class ImportedNutrition(_Contract):
    """Source-provided nutrition for a menu item."""

    serving_size: Decimal | None = None
    serving_unit: str | None = None
    nutrients: NutrientValues = Field(default_factory=NutrientValues)
    source_reference: str | None = None


class ImportedRecipeIngredient(_Contract):
    """One ingredient line of a recipe, as supplied by the source."""

    line_no: int
    original_text: str
    quantity: Decimal | None = None
    unit: str | None = None
    name: str | None = None
    preparation: str | None = None
    is_optional: bool = False
    #: Optional provider food id hint (deterministic match when present).
    external_food_id: str | None = None


class ImportedRecipe(_Contract):
    """A source recipe: yield, servings, and ordered ingredient lines."""

    source_system: str
    external_id: str | None = None
    yield_quantity: Decimal | None = None
    yield_unit: str | None = None
    servings: Decimal | None = None
    source_text: str | None = None
    ingredients: tuple[ImportedRecipeIngredient, ...] = ()


class ImportedMenuItem(_Contract):
    """A source menu item, possibly carrying provided nutrition and/or a recipe."""

    source_system: str
    external_id: str | None = None
    name: str
    description: str | None = None
    serving_size: Decimal | None = None
    serving_unit: str | None = None
    provided_nutrition: ImportedNutrition | None = None
    recipe: ImportedRecipe | None = None
    allergens: tuple[str, ...] = ()
    #: External id of the station this item is offered at (optional).
    station_external_id: str | None = None
    #: Offering placement (optional; enables offering upserts).
    service_date: date | None = None
    meal_period: MealPeriod | None = None
    source_metadata: dict[str, object] | None = None


class ImportedInstitution(_Contract):
    source_system: str
    external_id: str | None = None
    name: str
    slug: str
    institution_type: InstitutionType = InstitutionType.OTHER
    timezone: str = "UTC"


class ImportedVenue(_Contract):
    source_system: str
    external_id: str | None = None
    name: str
    slug: str
    venue_type: VenueType = VenueType.OTHER


class ImportedStation(_Contract):
    source_system: str
    external_id: str | None = None
    name: str
    slug: str
    #: External id of the parent venue.
    venue_external_id: str | None = None
    venue_slug: str | None = None
    station_type: str | None = None


class ImportPayload(_Contract):
    """A complete, source-neutral import payload."""

    institution: ImportedInstitution
    venues: tuple[ImportedVenue, ...] = ()
    stations: tuple[ImportedStation, ...] = ()
    menu_items: tuple[ImportedMenuItem, ...] = ()
