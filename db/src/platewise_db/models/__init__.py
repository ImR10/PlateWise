"""PlateWise ORM models.

Importing this package registers every model on ``Base.metadata`` so that
tooling (Alembic autogenerate, ``create_all``) sees the full schema from a
single import. Modules are grouped by domain:

    * ``institution`` -- institutions (top-level tenant)
    * ``location``    -- venues, stations (service hierarchy)
    * ``catalog``     -- menu items, aliases, nutrition, ingredients,
                         allergens, dietary tags, and their associations
    * ``menu``        -- menu offerings (item placements in time)
    * ``reports``     -- offering reports, menu-item suggestions
    * ``imports``     -- data imports (ingestion tracking)
"""

from platewise_db.models.catalog import (
    Allergen,
    DietaryTag,
    Ingredient,
    MenuItem,
    MenuItemAlias,
    MenuItemAllergen,
    MenuItemDietaryTag,
    MenuItemIngredient,
    NutritionFacts,
)
from platewise_db.models.imports import DataImport, DataImportError
from platewise_db.models.institution import Institution
from platewise_db.models.location import Station, Venue
from platewise_db.models.menu import MenuOffering
from platewise_db.models.providers import ProviderFood, ProviderFoodPortion
from platewise_db.models.recipes import RecipeIngredient, RecipeVersion
from platewise_db.models.reports import MenuItemSuggestion, OfferingReport

__all__ = [
    "Allergen",
    "DataImport",
    "DataImportError",
    "DietaryTag",
    "Ingredient",
    "Institution",
    "MenuItem",
    "MenuItemAlias",
    "MenuItemAllergen",
    "MenuItemDietaryTag",
    "MenuItemIngredient",
    "MenuItemSuggestion",
    "MenuOffering",
    "NutritionFacts",
    "OfferingReport",
    "ProviderFood",
    "ProviderFoodPortion",
    "RecipeIngredient",
    "RecipeVersion",
    "Station",
    "Venue",
]
