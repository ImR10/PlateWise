"""Source-neutral import contracts (Pydantic v2 DTOs).

Source adapters convert provider-specific payloads (JSON/CSV/...) into these
DTOs before anything else in the pipeline runs. Nothing downstream --
classification, normalization, calculation, or persistence -- may depend on a
source's native structure.

All numeric quantities are ``Decimal`` (see :mod:`platewise_db.decimal_utils`).
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Annotated

from platewise_db.enums import InstitutionType, MealPeriod, VenueType
from pydantic import BaseModel, ConfigDict, Field

MAX_SOURCE_SYSTEM_LENGTH = 100
MAX_EXTERNAL_ID_LENGTH = 255
MAX_NAME_LENGTH = 255
MAX_DESCRIPTION_LENGTH = 10_000
MAX_SOURCE_TEXT_LENGTH = 100_000
MAX_INGREDIENT_TEXT_LENGTH = 2_000
MAX_RECIPE_INGREDIENTS = 500
MAX_ALLERGENS = 100

# These maxima fit the corresponding SQL Numeric columns after quantization.
NutrientDecimal = Annotated[Decimal, Field(ge=0, le=Decimal("99999999.99"), allow_inf_nan=False)]
QuantityDecimal = Annotated[Decimal, Field(ge=0, le=Decimal("99999999.9999"), allow_inf_nan=False)]
ServingDecimal = Annotated[Decimal, Field(ge=0, le=Decimal("9999999.999"), allow_inf_nan=False)]


class _Contract(BaseModel):
    """Base config: strict-ish, immutable, forbids unknown fields."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class NutrientValues(_Contract):
    """The nutrients PlateWise tracks. Any nutrient may be ``None`` (unknown).

    A missing nutrient is ``None`` and is never coerced to zero.
    """

    calories: NutrientDecimal | None = None
    protein_g: NutrientDecimal | None = None
    carbohydrates_g: NutrientDecimal | None = None
    fat_g: NutrientDecimal | None = None
    saturated_fat_g: NutrientDecimal | None = None
    fiber_g: NutrientDecimal | None = None
    sugar_g: NutrientDecimal | None = None
    sodium_mg: NutrientDecimal | None = None
    cholesterol_mg: NutrientDecimal | None = None


class ImportedNutrition(_Contract):
    """Source-provided nutrition for a menu item."""

    serving_size: ServingDecimal | None = None
    serving_unit: str | None = Field(default=None, max_length=50)
    nutrients: NutrientValues = Field(default_factory=NutrientValues)
    source_reference: str | None = Field(default=None, max_length=MAX_EXTERNAL_ID_LENGTH)


class ImportedRecipeIngredient(_Contract):
    """One ingredient line of a recipe, as supplied by the source."""

    line_no: int = Field(ge=0, le=100_000)
    original_text: str = Field(min_length=1, max_length=MAX_INGREDIENT_TEXT_LENGTH)
    quantity: QuantityDecimal | None = None
    unit: str | None = Field(default=None, max_length=50)
    name: str | None = Field(default=None, max_length=MAX_NAME_LENGTH)
    preparation: str | None = Field(default=None, max_length=MAX_INGREDIENT_TEXT_LENGTH)
    is_optional: bool = False
    #: Optional provider food id hint (deterministic match when present).
    external_food_id: str | None = Field(default=None, max_length=MAX_EXTERNAL_ID_LENGTH)


class ImportedRecipe(_Contract):
    """A source recipe: yield, servings, and ordered ingredient lines."""

    source_system: str = Field(min_length=1, max_length=MAX_SOURCE_SYSTEM_LENGTH)
    external_id: str | None = Field(default=None, max_length=MAX_EXTERNAL_ID_LENGTH)
    yield_quantity: QuantityDecimal | None = None
    yield_unit: str | None = Field(default=None, max_length=50)
    servings: QuantityDecimal | None = None
    source_text: str | None = Field(default=None, max_length=MAX_SOURCE_TEXT_LENGTH)
    ingredients: tuple[ImportedRecipeIngredient, ...] = Field(
        default=(), max_length=MAX_RECIPE_INGREDIENTS
    )


class ImportedMenuItem(_Contract):
    """A source menu item, possibly carrying provided nutrition and/or a recipe."""

    source_system: str = Field(min_length=1, max_length=MAX_SOURCE_SYSTEM_LENGTH)
    external_id: str | None = Field(default=None, max_length=MAX_EXTERNAL_ID_LENGTH)
    name: str = Field(max_length=MAX_NAME_LENGTH)
    description: str | None = Field(default=None, max_length=MAX_DESCRIPTION_LENGTH)
    serving_size: ServingDecimal | None = None
    serving_unit: str | None = Field(default=None, max_length=50)
    provided_nutrition: ImportedNutrition | None = None
    recipe: ImportedRecipe | None = None
    allergens: tuple[str, ...] = Field(default=(), max_length=MAX_ALLERGENS)
    #: External id of the station this item is offered at (optional).
    station_external_id: str | None = Field(default=None, max_length=MAX_EXTERNAL_ID_LENGTH)
    #: Offering placement (optional; enables offering upserts).
    service_date: date | None = None
    meal_period: MealPeriod | None = None
    source_metadata: dict[str, object] | None = Field(default=None, max_length=100)


class ImportedInstitution(_Contract):
    source_system: str = Field(min_length=1, max_length=MAX_SOURCE_SYSTEM_LENGTH)
    external_id: str | None = Field(default=None, max_length=MAX_EXTERNAL_ID_LENGTH)
    name: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)
    slug: str = Field(min_length=1, max_length=255)
    institution_type: InstitutionType = InstitutionType.OTHER
    timezone: str = Field(default="UTC", min_length=1, max_length=100)


class ImportedVenue(_Contract):
    source_system: str = Field(min_length=1, max_length=MAX_SOURCE_SYSTEM_LENGTH)
    external_id: str | None = Field(default=None, max_length=MAX_EXTERNAL_ID_LENGTH)
    name: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)
    slug: str = Field(min_length=1, max_length=255)
    venue_type: VenueType = VenueType.OTHER


class ImportedStation(_Contract):
    source_system: str = Field(min_length=1, max_length=MAX_SOURCE_SYSTEM_LENGTH)
    external_id: str | None = Field(default=None, max_length=MAX_EXTERNAL_ID_LENGTH)
    name: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)
    slug: str = Field(min_length=1, max_length=255)
    #: External id of the parent venue.
    venue_external_id: str | None = Field(default=None, max_length=MAX_EXTERNAL_ID_LENGTH)
    venue_slug: str | None = Field(default=None, max_length=255)
    station_type: str | None = Field(default=None, max_length=100)


class ImportPayload(_Contract):
    """A complete, source-neutral import payload."""

    institution: ImportedInstitution
    venues: tuple[ImportedVenue, ...] = ()
    stations: tuple[ImportedStation, ...] = ()
    menu_items: tuple[ImportedMenuItem, ...] = ()
