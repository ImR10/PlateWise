"""Versioned recipe storage -- the calculation inputs for recipe nutrition.

    MenuItem -> RecipeVersion -> RecipeIngredient -> (ProviderFood)

These tables are distinct in responsibility from ``menu_item_ingredients``:

* ``RecipeIngredient`` records are *versioned calculation inputs*. They preserve
  the original source text, the parsed quantity/unit, the gram conversion, the
  resolved canonical (provider) food, and the full resolution/match provenance
  needed to make recipe-calculated nutrition traceable and reproducible.
* ``menu_item_ingredients`` remains the simplified, catalog-facing "what is in
  this dish" link used for dietary/allergen review.

Authoritative recipe-calculation state lives here; the catalog link stays
lightweight and is not treated as a calculation input.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.enums import (
    IngredientMatchMethod,
    IngredientResolutionStatus,
    RawOrCooked,
    pg_enum,
)
from app.db.mixins import SourceTrackingMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.catalog import Ingredient, MenuItem, NutritionFacts
    from app.db.models.imports import DataImport
    from app.db.models.providers import ProviderFood

# Higher-scale precision for calculation-critical quantities and gram weights.
_QUANTITY4 = Numeric(12, 4)

UNKNOWN_SOURCE_SYSTEM = "unknown"


class RecipeVersion(UUIDPrimaryKeyMixin, TimestampMixin, SourceTrackingMixin, Base):
    """One version of a menu item's recipe (yield, servings, ingredient lines).

    Recipes are versioned like nutrition: a meaningful content change creates a
    new version and supersedes the previous one (``valid_until`` set), so
    historical calculation provenance is never destroyed.
    """

    __tablename__ = "recipe_versions"
    __table_args__ = (
        UniqueConstraint(
            "menu_item_id", "version_no", name="uq_recipe_versions_menu_item_id_version_no"
        ),
        # One active recipe version per menu item. (Recipe idempotency keys on
        # the active version + content_hash; the source recipe ``external_id`` is
        # provenance only and is intentionally NOT globally unique, since many
        # versions over time share the same source recipe id.)
        Index(
            "uq_recipe_versions_active_per_menu_item",
            "menu_item_id",
            unique=True,
            postgresql_where=text("valid_until IS NULL"),
        ),
        Index(
            "ix_recipe_versions_menu_item_id_source_system_external_id",
            "menu_item_id",
            "source_system",
            "external_id",
        ),
    )

    menu_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("menu_items.id", ondelete="CASCADE"), nullable=False
    )
    source_system: Mapped[str] = mapped_column(
        String(100), nullable=False, server_default=UNKNOWN_SOURCE_SYSTEM
    )
    #: Source recipe identifier, when the source provides one.
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    version_no: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")

    #: Total recipe yield and the units it is expressed in (may be NULL).
    yield_quantity: Mapped[Decimal | None] = mapped_column(_QUANTITY4, nullable=True)
    yield_unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    #: Number of servings the recipe produces (divisor for per-serving nutrition).
    servings: Mapped[Decimal | None] = mapped_column(_QUANTITY4, nullable=True)

    #: Original recipe text, preserved for debugging/reproduction.
    source_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    #: ``NULL`` marks the currently-active version.
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_by_import_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("data_imports.id", ondelete="SET NULL"), nullable=True
    )

    # --- Relationships -----------------------------------------------------
    menu_item: Mapped[MenuItem] = relationship(back_populates="recipe_versions")
    ingredients: Mapped[list[RecipeIngredient]] = relationship(
        back_populates="recipe_version",
        cascade="all, delete-orphan",
        order_by="RecipeIngredient.line_no",
    )
    calculated_nutrition: Mapped[list[NutritionFacts]] = relationship(
        back_populates="recipe_version",
        foreign_keys="NutritionFacts.recipe_version_id",
        passive_deletes=True,
    )
    created_by_import: Mapped[DataImport | None] = relationship(foreign_keys=[created_by_import_id])

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<RecipeVersion menu_item_id={self.menu_item_id} v{self.version_no}>"


class RecipeIngredient(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A single ingredient line within a recipe version, with full resolution state."""

    __tablename__ = "recipe_ingredients"
    __table_args__ = (
        UniqueConstraint(
            "recipe_version_id", "line_no", name="uq_recipe_ingredients_recipe_version_id_line_no"
        ),
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="confidence_range",
        ),
        Index("ix_recipe_ingredients_recipe_version_id", "recipe_version_id"),
        Index("ix_recipe_ingredients_provider_food_id", "provider_food_id"),
    )

    recipe_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("recipe_versions.id", ondelete="CASCADE"), nullable=False
    )
    #: Position of this line in the original recipe (source order).
    line_no: Mapped[int] = mapped_column(Integer, nullable=False)

    #: Verbatim source text of the ingredient line (always preserved).
    original_text: Mapped[str] = mapped_column(Text, nullable=False)

    parsed_quantity: Mapped[Decimal | None] = mapped_column(_QUANTITY4, nullable=True)
    parsed_unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    normalized_ingredient_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    preparation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_optional: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    raw_or_cooked: Mapped[RawOrCooked | None] = mapped_column(
        pg_enum(RawOrCooked, "raw_or_cooked"), nullable=True
    )

    #: Quantity converted to edible grams (NULL when not convertible).
    grams: Mapped[Decimal | None] = mapped_column(_QUANTITY4, nullable=True)

    #: Institution catalog ingredient (soft reference).
    ingredient_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("ingredients.id", ondelete="SET NULL"), nullable=True
    )
    #: Resolved canonical provider food used for nutrient composition.
    provider_food_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("provider_foods.id", ondelete="SET NULL"), nullable=True
    )

    match_method: Mapped[IngredientMatchMethod | None] = mapped_column(
        pg_enum(IngredientMatchMethod, "ingredient_match_method"), nullable=True
    )
    resolution_status: Mapped[IngredientResolutionStatus] = mapped_column(
        pg_enum(IngredientResolutionStatus, "ingredient_resolution_status"),
        nullable=False,
        server_default=IngredientResolutionStatus.NEEDS_REVIEW.value,
    )
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    #: Human-readable reason when the line could not be resolved.
    error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)

    # --- Relationships -----------------------------------------------------
    recipe_version: Mapped[RecipeVersion] = relationship(back_populates="ingredients")
    ingredient: Mapped[Ingredient | None] = relationship(foreign_keys=[ingredient_id])
    provider_food: Mapped[ProviderFood | None] = relationship(foreign_keys=[provider_food_id])

    @property
    def is_resolved(self) -> bool:
        """True only when the line contributes trusted nutrition to the recipe."""
        return self.resolution_status == IngredientResolutionStatus.RESOLVED

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<RecipeIngredient line={self.line_no} status={self.resolution_status!r}>"
