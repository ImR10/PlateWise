"""Ingredient-nutrition provider cache.

The recipe calculator resolves ingredients against an *ingredient-nutrition
provider* -- a source of canonical foods with nutrient composition, kept
deliberately separate from the dining-data source. These tables cache the
provider's foods and their supported portion weights so recipe calculations are
deterministic and reproducible.

Nutrient composition is stored on a known reference basis (per 100 g). Important
identifiers and calculation fields are normalized and constrained; opaque
provider metadata may be retained in ``raw_metadata`` (JSONB).
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import ForeignKey, Index, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import SourceTrackingMixin, TimestampMixin, UUIDPrimaryKeyMixin

# Nutrient composition uses higher scale (per-100 g reference values).
_PER_100G = Numeric(12, 4)
_GRAMS = Numeric(12, 4)


class ProviderFood(UUIDPrimaryKeyMixin, TimestampMixin, SourceTrackingMixin, Base):
    """A canonical food from an ingredient-nutrition provider, cached locally.

    Nutrients are expressed per ``reference_grams`` (default 100 g), so a
    contribution is ``nutrient_per_100g * grams / 100``.
    """

    __tablename__ = "provider_foods"
    __table_args__ = (
        UniqueConstraint(
            "provider", "provider_food_id", name="uq_provider_foods_provider_provider_food_id"
        ),
    )

    #: Provider identity (e.g. "fake", and later a real provider key).
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    #: The provider's own identifier for this food.
    provider_food_id: Mapped[str] = mapped_column(String(255), nullable=False)

    #: Canonical / display name.
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    #: Reference basis for the nutrient columns (grams). Default 100 g.
    reference_grams: Mapped[Decimal] = mapped_column(
        _GRAMS, nullable=False, server_default="100"
    )

    # Nutrient composition per ``reference_grams``. Missing nutrients stay NULL.
    calories: Mapped[Decimal | None] = mapped_column(_PER_100G, nullable=True)
    protein_g: Mapped[Decimal | None] = mapped_column(_PER_100G, nullable=True)
    carbohydrates_g: Mapped[Decimal | None] = mapped_column(_PER_100G, nullable=True)
    fat_g: Mapped[Decimal | None] = mapped_column(_PER_100G, nullable=True)
    saturated_fat_g: Mapped[Decimal | None] = mapped_column(_PER_100G, nullable=True)
    fiber_g: Mapped[Decimal | None] = mapped_column(_PER_100G, nullable=True)
    sugar_g: Mapped[Decimal | None] = mapped_column(_PER_100G, nullable=True)
    sodium_mg: Mapped[Decimal | None] = mapped_column(_PER_100G, nullable=True)
    cholesterol_mg: Mapped[Decimal | None] = mapped_column(_PER_100G, nullable=True)

    #: Opaque provider payload retained for debugging/traceability.
    raw_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    portions: Mapped[list[ProviderFoodPortion]] = relationship(
        back_populates="provider_food", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<ProviderFood provider={self.provider!r} id={self.provider_food_id!r}>"


class ProviderFoodPortion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A named portion for a provider food and its weight in grams.

    Enables portion-to-gram conversion using a *resolved provider weight* rather
    than a guessed density.
    """

    __tablename__ = "provider_food_portions"
    __table_args__ = (
        UniqueConstraint(
            "provider_food_id",
            "portion_description",
            name="uq_provider_food_portions_provider_food_id_portion_description",
        ),
        Index("ix_provider_food_portions_provider_food_id", "provider_food_id"),
    )

    provider_food_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("provider_foods.id", ondelete="CASCADE"), nullable=False
    )
    #: e.g. "1 medium", "1 cup", "1 breast".
    portion_description: Mapped[str] = mapped_column(String(255), nullable=False)
    gram_weight: Mapped[Decimal] = mapped_column(_GRAMS, nullable=False)

    provider_food: Mapped[ProviderFood] = relationship(back_populates="portions")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<ProviderFoodPortion {self.portion_description!r}={self.gram_weight}g>"
