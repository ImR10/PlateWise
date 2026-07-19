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
from typing import Annotated, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.imports.contracts import NutrientValues
from app.imports.normalizers import normalize_name


class ProviderPortion(BaseModel):
    """A named portion for a provider food and its weight in grams."""

    model_config = ConfigDict(frozen=True)

    description: str = Field(min_length=1, max_length=255)
    gram_weight: Annotated[
        Decimal, Field(gt=0, le=Decimal("99999999.9999"), allow_inf_nan=False)
    ]


class ProviderFoodData(BaseModel):
    """A canonical food returned by an ingredient-nutrition provider.

    Nutrients are expressed per ``reference_grams`` (default 100 g).
    """

    model_config = ConfigDict(frozen=True)

    provider: str = Field(min_length=1, max_length=100)
    provider_food_id: str = Field(min_length=1, max_length=255)
    name: str = Field(min_length=1, max_length=255)
    reference_grams: Annotated[
        Decimal, Field(gt=0, le=Decimal("99999999.9999"), allow_inf_nan=False)
    ] = Decimal("100")
    nutrients: NutrientValues = Field(default_factory=NutrientValues)
    portions: tuple[ProviderPortion, ...] = Field(default=(), max_length=500)
    #: Extra provider aliases that should also match ``search_food``.
    search_aliases: tuple[str, ...] = Field(default=(), max_length=500)
    raw_metadata: dict[str, object] | None = Field(default=None, max_length=100)

    @model_validator(mode="after")
    def portion_descriptions_are_unique(self) -> ProviderFoodData:
        descriptions = [normalize_name(portion.description) for portion in self.portions]
        if len(descriptions) != len(set(descriptions)):
            raise ValueError("duplicate normalized provider portion description")
        return self


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
            if food.provider != provider_name:
                raise ValueError(
                    f"food provider {food.provider!r} does not match provider {provider_name!r}"
                )
            if food.provider_food_id in self._by_id:
                raise ValueError(f"duplicate provider food id: {food.provider_food_id!r}")
            self._by_id[food.provider_food_id] = food
            self._add_search_key(food.name, food)
            for alias in food.search_aliases:
                self._add_search_key(alias, food)

    def _add_search_key(self, value: str, food: ProviderFoodData) -> None:
        key = normalize_name(value)
        existing = self._by_name.get(key)
        if existing is not None and existing.provider_food_id != food.provider_food_id:
            raise ValueError(f"ambiguous provider food name/alias: {value!r}")
        self._by_name[key] = food

    @property
    def provider_name(self) -> str:
        return self._provider_name

    def get_food(self, external_food_id: str) -> ProviderFoodData | None:
        return self._by_id.get(external_food_id)

    def search_food(self, query: str) -> ProviderFoodData | None:
        return self._by_name.get(normalize_name(query))


class CachingIngredientNutritionProvider:
    """Small run-scoped cache for deterministic provider lookups."""

    def __init__(self, provider: IngredientNutritionProvider) -> None:
        self._provider = provider
        self._by_id: dict[str, ProviderFoodData | None] = {}
        self._by_query: dict[str, ProviderFoodData | None] = {}

    @property
    def provider_name(self) -> str:
        return self._provider.provider_name

    def get_food(self, external_food_id: str) -> ProviderFoodData | None:
        if external_food_id not in self._by_id:
            self._by_id[external_food_id] = self._provider.get_food(external_food_id)
        return self._by_id[external_food_id]

    def search_food(self, query: str) -> ProviderFoodData | None:
        key = normalize_name(query)
        if key not in self._by_query:
            self._by_query[key] = self._provider.search_food(query)
        return self._by_query[key]
