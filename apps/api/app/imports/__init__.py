"""PlateWise data-import foundation.

Public entry points for running an import and for the two external boundaries
(dining source, ingredient-nutrition provider). See ``docs/data-import-architecture.md``.
"""

from app.imports.enums import RecordClassification
from app.imports.exceptions import (
    ImportError_,
    MalformedRecordError,
    RecordPersistenceError,
    SourceError,
)
from app.imports.nutrition.provider import (
    FakeIngredientNutritionProvider,
    IngredientNutritionProvider,
    ProviderFoodData,
    ProviderPortion,
)
from app.imports.service import ImportCounters, ImportResult, run_import
from app.imports.sources.base import DiningSource, FetchResult
from app.imports.sources.fixture import FixtureDiningSource

__all__ = [
    "DiningSource",
    "FakeIngredientNutritionProvider",
    "FetchResult",
    "FixtureDiningSource",
    "ImportError_",
    "ImportCounters",
    "ImportResult",
    "IngredientNutritionProvider",
    "MalformedRecordError",
    "ProviderFoodData",
    "ProviderPortion",
    "RecordClassification",
    "RecordPersistenceError",
    "SourceError",
    "run_import",
]
