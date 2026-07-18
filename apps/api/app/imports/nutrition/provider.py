"""Ingredient-nutrition provider boundary.

This is deliberately separate from the dining-data source: it supplies canonical
foods with nutrient composition and portion weights for recipe calculation.

The MVP ships **only** a ``Protocol`` and a deterministic in-memory fake. No real
external API/dataset is integrated; a future network-backed provider implements
the same synchronous ``Protocol`` and can add its own caching/retry without
changing the pipeline.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

from app.imports.contracts import NutrientValues
from app.imports.normalizers import normalize_name


class ProviderPortion(BaseModel):
    """A named portion for a provider food and its weight in grams."""

    model_config = ConfigDict(frozen=True)

    description: str
    gram_weight: Decimal


class ProviderFoodData(BaseModel):
    """A canonical food returned by an ingredient-nutrition provider.

    Nutrients are expressed per ``reference_grams`` (default 100 g).
    """

    model_config = ConfigDict(frozen=True)

    provider: str
    provider_food_id: str
    name: str
    reference_grams: Decimal = Decimal("100")
    nutrients: NutrientValues = Field(default_factory=NutrientValues)
    portions: tuple[ProviderPortion, ...] = ()
    #: Extra provider aliases that should also match ``search_food``.
    search_aliases: tuple[str, ...] = ()
    raw_metadata: dict[str, object] | None = None


@runtime_checkable
class IngredientNutritionProvider(Protocol):
    """Synchronous provider interface used by the ingredient resolver."""

    @property
    def provider_name(self) -> str: ...

    def get_food(self, external_food_id: str) -> ProviderFoodData | None:
        """Return the food with this provider id, or ``None`` if unknown."""

    def search_food(self, query: str) -> ProviderFoodData | None:
        """Return the best canonical match for ``query``, or ``None``.

        Fuzzy/uncontrolled matching must never be used as an authoritative
        persistence key; deterministic lookups are preferred.
        """


class FakeIngredientNutritionProvider:
    """Deterministic in-memory provider for fixtures and tests.

    Lookups are exact (by provider food id, or by normalized name/alias) so the
    entire recipe-calculation path is reproducible without any network access.
    """

    def __init__(self, foods: list[ProviderFoodData], *, provider_name: str = "fake") -> None:
        self._provider_name = provider_name
        self._by_id: dict[str, ProviderFoodData] = {}
        self._by_name: dict[str, ProviderFoodData] = {}
        for food in foods:
            self._by_id[food.provider_food_id] = food
            self._by_name[normalize_name(food.name)] = food
            for alias in food.search_aliases:
                self._by_name[normalize_name(alias)] = food

    @property
    def provider_name(self) -> str:
        return self._provider_name

    def get_food(self, external_food_id: str) -> ProviderFoodData | None:
        return self._by_id.get(external_food_id)

    def search_food(self, query: str) -> ProviderFoodData | None:
        return self._by_name.get(normalize_name(query))
