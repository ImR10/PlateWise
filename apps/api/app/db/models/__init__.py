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

from app.db.models.catalog import (
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
from app.db.models.imports import DataImport
from app.db.models.institution import Institution
from app.db.models.location import Station, Venue
from app.db.models.menu import MenuOffering
from app.db.models.reports import MenuItemSuggestion, OfferingReport

__all__ = [
    "Allergen",
    "DataImport",
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
    "Station",
    "Venue",
]
