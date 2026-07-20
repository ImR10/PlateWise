"""PlateWise data-import foundation.

Public entry points for running an import and for the two external boundaries
(dining source, ingredient-nutrition provider). See ``docs/data-import-architecture.md``.
"""

from platewise_api.imports.enums import RecordClassification
from platewise_api.imports.exceptions import (
    ImportError_,
    MalformedRecordError,
    RecordPersistenceError,
    SourceError,
)
from platewise_api.imports.nutrition.provider import (
    FakeIngredientNutritionProvider,
    IngredientNutritionProvider,
    ProviderFoodData,
    ProviderPortion,
)
from platewise_api.imports.service import ImportCounters, ImportResult, run_import
from platewise_api.imports.sources.base import DiningSource, FetchResult
from platewise_api.imports.sources.fixture import FixtureDiningSource

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
