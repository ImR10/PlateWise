"""Institution-owned menu-item catalog.

This module holds the persistent record of *what a food is*, independent of
where or when it is served:

    * ``MenuItem``            -- a food product / prepared dish
    * ``MenuItemAlias``       -- alternate names for search & matching
    * ``NutritionFacts``      -- versioned nutrition for a menu item
    * ``Ingredient``          -- institution-owned ingredient catalog
    * ``MenuItemIngredient``  -- menu item <-> ingredient (association object)
    * ``Allergen``            -- normalized allergen catalog (global)
    * ``MenuItemAllergen``    -- menu item <-> allergen declaration
    * ``DietaryTag``          -- normalized dietary-tag catalog (global)
    * ``MenuItemDietaryTag``  -- menu item <-> dietary tag

Catalog records persist even when an item is not currently served; they are
archived rather than deleted.
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
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.orm import Mapped, mapped_column, relationship

from platewise_db.base import Base
from platewise_db.enums import (
    AllergenDeclarationType,
    CalculationStatus,
    NutritionProvenance,
    NutritionReviewStatus,
    NutritionSourceType,
    ProvenanceSourceType,
    pg_enum,
)
from platewise_db.mixins import SourceTrackingMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from platewise_db.models.imports import DataImport
    from platewise_db.models.institution import Institution
    from platewise_db.models.menu import MenuOffering
    from platewise_db.models.recipes import RecipeVersion

# Money/measurement precision for nutrition and recipe quantities. Columns are
# SQL ``Numeric`` (mapped to Python ``Decimal``) so nutrition arithmetic stays
# exact and deterministic -- never binary floating point.
_QUANTITY = Numeric(10, 3)
_NUTRIENT = Numeric(10, 2)

# Default source-system marker for rows whose external origin is unknown
# (e.g. rows created before multi-source identity existed, or created by hand).
UNKNOWN_SOURCE_SYSTEM = "unknown"


class MenuItem(UUIDPrimaryKeyMixin, TimestampMixin, SourceTrackingMixin, Base):
    """A persistent catalog record for a food product or prepared dish."""

    __tablename__ = "menu_items"
    __table_args__ = (
        # Deterministic external identity for idempotent upserts:
        # UNIQUE(institution_id, source_system, external_id) *only* where an
        # external id exists. Multiple NULL external ids per institution are
        # allowed (name is intentionally NOT a uniqueness key -- two distinct
        # items may share a name).
        Index(
            "uq_menu_items_institution_id_source_system_external_id",
            "institution_id",
            "source_system",
            "external_id",
            unique=True,
            postgresql_where=text("external_id IS NOT NULL"),
        ),
        Index("ix_menu_items_institution_id_normalized_name", "institution_id", "normalized_name"),
    )

    institution_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False
    )
    #: External source system this item was imported from (e.g. "nutrislice").
    source_system: Mapped[str] = mapped_column(
        String(100), nullable=False, server_default=UNKNOWN_SOURCE_SYSTEM
    )
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    #: Search-friendly normalized form of ``name`` (e.g. lowercased/trimmed).
    normalized_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    default_serving_size: Mapped[Decimal | None] = mapped_column(_QUANTITY, nullable=True)
    default_serving_unit: Mapped[str | None] = mapped_column(String(50), nullable=True)

    #: The institution may still serve the item (not tied to today's menu).
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    #: Reserved for duplicates, invalid records, and manual cleanup.
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    created_by_import_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("data_imports.id", ondelete="SET NULL"), nullable=True
    )
    updated_by_import_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("data_imports.id", ondelete="SET NULL"), nullable=True
    )

    # --- Relationships -----------------------------------------------------
    institution: Mapped[Institution] = relationship(back_populates="menu_items")

    aliases: Mapped[list[MenuItemAlias]] = relationship(
        back_populates="menu_item", cascade="all, delete-orphan"
    )
    nutrition_facts: Mapped[list[NutritionFacts]] = relationship(
        back_populates="menu_item",
        cascade="all, delete-orphan",
        order_by="NutritionFacts.valid_from",
    )
    ingredient_links: Mapped[list[MenuItemIngredient]] = relationship(
        back_populates="menu_item", cascade="all, delete-orphan"
    )
    allergen_links: Mapped[list[MenuItemAllergen]] = relationship(
        back_populates="menu_item", cascade="all, delete-orphan"
    )
    dietary_tag_links: Mapped[list[MenuItemDietaryTag]] = relationship(
        back_populates="menu_item", cascade="all, delete-orphan"
    )
    offerings: Mapped[list[MenuOffering]] = relationship(
        back_populates="menu_item",
        foreign_keys="MenuOffering.menu_item_id",
        passive_deletes=True,
    )
    recipe_versions: Mapped[list[RecipeVersion]] = relationship(
        back_populates="menu_item",
        cascade="all, delete-orphan",
        order_by="RecipeVersion.version_no",
    )

    created_by_import: Mapped[DataImport | None] = relationship(
        back_populates="created_menu_items", foreign_keys=[created_by_import_id]
    )
    updated_by_import: Mapped[DataImport | None] = relationship(foreign_keys=[updated_by_import_id])

    # Convenience proxies straight through the association objects.
    ingredients: AssociationProxy[list[Ingredient]] = association_proxy(
        "ingredient_links", "ingredient"
    )
    allergens: AssociationProxy[list[Allergen]] = association_proxy("allergen_links", "allergen")
    dietary_tags: AssociationProxy[list[DietaryTag]] = association_proxy(
        "dietary_tag_links", "dietary_tag"
    )

    @property
    def active_nutrition(self) -> list[NutritionFacts]:
        """All currently-active nutrition records (``valid_until IS NULL``)."""
        return [facts for facts in self.nutrition_facts if facts.valid_until is None]

    @property
    def active_recipe_version(self) -> RecipeVersion | None:
        """The single active recipe version, if any."""
        for version in self.recipe_versions:
            if version.valid_until is None:
                return version
        return None

    def display_nutrition(self) -> NutritionFacts | None:
        """Return the nutrition record to show users.

        MVP precedence (see docs/recipe-nutrition-calculation.md):

        1. active source-provided nutrition is preferred;
        2. active recipe-calculated nutrition is the fallback, but only when it
           is complete -- incomplete calculated nutrition is never authoritative;
        3. otherwise no authoritative nutrition is available (``None``).
        """
        active = self.active_nutrition
        for facts in active:
            if facts.provenance == NutritionProvenance.SOURCE_PROVIDED:
                return facts
        for facts in active:
            if facts.provenance == NutritionProvenance.RECIPE_CALCULATED and facts.is_complete:
                return facts
        return None

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<MenuItem name={self.name!r}>"


class MenuItemAlias(UUIDPrimaryKeyMixin, Base):
    """An alternate name a menu item is also known by."""

    __tablename__ = "menu_item_aliases"
    __table_args__ = (
        UniqueConstraint(
            "menu_item_id",
            "normalized_alias",
            name="uq_menu_item_aliases_menu_item_id_normalized_alias",
        ),
        Index("ix_menu_item_aliases_menu_item_id", "menu_item_id"),
        Index("ix_menu_item_aliases_normalized_alias", "normalized_alias"),
    )

    menu_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("menu_items.id", ondelete="CASCADE"), nullable=False
    )
    alias: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_alias: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[ProvenanceSourceType] = mapped_column(
        pg_enum(ProvenanceSourceType, "alias_source_type"),
        nullable=False,
        server_default=ProvenanceSourceType.IMPORTED.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    menu_item: Mapped[MenuItem] = relationship(back_populates="aliases")


class NutritionFacts(UUIDPrimaryKeyMixin, TimestampMixin, SourceTrackingMixin, Base):
    """Nutrition for a menu item, versioned via ``valid_from`` / ``valid_until``.

    Source-provided and recipe-calculated nutrition **coexist**: at most one
    *active* record (``valid_until IS NULL``) exists per
    ``(menu_item_id, provenance)``, so neither overwrites the other. Superseded
    versions are retained for history.

    Nutrient values are ``Decimal`` and nullable -- a missing nutrient stays
    ``NULL`` and is never coerced to zero.
    """

    __tablename__ = "nutrition_facts"
    __table_args__ = (
        Index(
            "ix_nutrition_facts_menu_item_id_valid_from_valid_until",
            "menu_item_id",
            "valid_from",
            "valid_until",
        ),
        # One active nutrition record per (menu item, provenance) so that
        # source-provided and recipe-calculated nutrition can both be active.
        Index(
            "uq_nutrition_facts_active_per_menu_item_provenance",
            "menu_item_id",
            "provenance",
            unique=True,
            postgresql_where=text("valid_until IS NULL"),
        ),
    )

    menu_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("menu_items.id", ondelete="CASCADE"), nullable=False
    )

    #: Coexistence discriminator: how this nutrition was obtained.
    provenance: Mapped[NutritionProvenance] = mapped_column(
        pg_enum(NutritionProvenance, "nutrition_provenance"),
        nullable=False,
        server_default=NutritionProvenance.SOURCE_PROVIDED.value,
    )

    serving_size: Mapped[Decimal | None] = mapped_column(_QUANTITY, nullable=True)
    serving_unit: Mapped[str | None] = mapped_column(String(50), nullable=True)

    calories: Mapped[Decimal | None] = mapped_column(_NUTRIENT, nullable=True)
    protein_g: Mapped[Decimal | None] = mapped_column(_NUTRIENT, nullable=True)
    carbohydrates_g: Mapped[Decimal | None] = mapped_column(_NUTRIENT, nullable=True)
    fat_g: Mapped[Decimal | None] = mapped_column(_NUTRIENT, nullable=True)
    saturated_fat_g: Mapped[Decimal | None] = mapped_column(_NUTRIENT, nullable=True)
    fiber_g: Mapped[Decimal | None] = mapped_column(_NUTRIENT, nullable=True)
    sugar_g: Mapped[Decimal | None] = mapped_column(_NUTRIENT, nullable=True)
    sodium_mg: Mapped[Decimal | None] = mapped_column(_NUTRIENT, nullable=True)
    cholesterol_mg: Mapped[Decimal | None] = mapped_column(_NUTRIENT, nullable=True)

    source_type: Mapped[NutritionSourceType] = mapped_column(
        pg_enum(NutritionSourceType, "nutrition_source_type"),
        nullable=False,
        server_default=NutritionSourceType.OFFICIAL.value,
    )
    source_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_estimated: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    # --- Recipe-calculation provenance (populated only for calculated rows) ---
    #: Whether every nutrient in this record is backed by resolved inputs.
    #: Incomplete calculated nutrition must never be treated as authoritative.
    is_complete: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    review_status: Mapped[NutritionReviewStatus] = mapped_column(
        pg_enum(NutritionReviewStatus, "nutrition_review_status"),
        nullable=False,
        server_default=NutritionReviewStatus.NOT_REQUIRED.value,
    )
    calculation_status: Mapped[CalculationStatus | None] = mapped_column(
        pg_enum(CalculationStatus, "calculation_status"), nullable=True
    )
    #: Version tag of the calculation algorithm that produced this record.
    calculation_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    calculated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    #: The recipe version whose ingredient resolutions produced this nutrition.
    recipe_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("recipe_versions.id", ondelete="SET NULL"), nullable=True
    )

    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    #: ``NULL`` marks the currently-active version.
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_by_import_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("data_imports.id", ondelete="SET NULL"), nullable=True
    )
    updated_by_import_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("data_imports.id", ondelete="SET NULL"), nullable=True
    )

    menu_item: Mapped[MenuItem] = relationship(back_populates="nutrition_facts")
    recipe_version: Mapped[RecipeVersion | None] = relationship(
        back_populates="calculated_nutrition", foreign_keys=[recipe_version_id]
    )


class Ingredient(UUIDPrimaryKeyMixin, TimestampMixin, SourceTrackingMixin, Base):
    """An institution-owned, searchable ingredient record."""

    __tablename__ = "ingredients"
    __table_args__ = (
        # Deterministic name-based identity (institution-scoped fallback key).
        UniqueConstraint(
            "institution_id",
            "normalized_name",
            name="uq_ingredients_institution_id_normalized_name",
        ),
        # External identity for idempotent upserts when the source supplies one.
        Index(
            "uq_ingredients_institution_id_source_system_external_id",
            "institution_id",
            "source_system",
            "external_id",
            unique=True,
            postgresql_where=text("external_id IS NOT NULL"),
        ),
        Index("ix_ingredients_institution_id_normalized_name", "institution_id", "normalized_name"),
    )

    institution_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False
    )
    source_system: Mapped[str] = mapped_column(
        String(100), nullable=False, server_default=UNKNOWN_SOURCE_SYSTEM
    )
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    institution: Mapped[Institution] = relationship(back_populates="ingredients")
    menu_item_links: Mapped[list[MenuItemIngredient]] = relationship(
        back_populates="ingredient", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Ingredient name={self.name!r}>"


class MenuItemIngredient(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Association object linking a menu item to one of its ingredients.

    Quantity/unit may be ``NULL`` when a source lists ingredients without
    recipe amounts; the link is still useful for allergen and dietary review.
    """

    __tablename__ = "menu_item_ingredients"
    __table_args__ = (
        UniqueConstraint(
            "menu_item_id",
            "ingredient_id",
            name="uq_menu_item_ingredients_menu_item_id_ingredient_id",
        ),
        Index("ix_menu_item_ingredients_ingredient_id", "ingredient_id"),
    )

    menu_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("menu_items.id", ondelete="CASCADE"), nullable=False
    )
    ingredient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ingredients.id", ondelete="CASCADE"), nullable=False
    )

    quantity: Mapped[Decimal | None] = mapped_column(_QUANTITY, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    preparation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_estimated: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    menu_item: Mapped[MenuItem] = relationship(back_populates="ingredient_links")
    ingredient: Mapped[Ingredient] = relationship(back_populates="menu_item_links")


class Allergen(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A normalized allergen (milk, egg, peanut, ...), shared across institutions."""

    __tablename__ = "allergens"
    __table_args__ = (UniqueConstraint("normalized_name", name="uq_allergens_normalized_name"),)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(100), nullable=False)

    menu_item_links: Mapped[list[MenuItemAllergen]] = relationship(
        back_populates="allergen", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Allergen name={self.name!r}>"


class MenuItemAllergen(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """An allergen declaration attached to a menu item.

    Absence of a declaration must never be treated as "allergen free".
    """

    __tablename__ = "menu_item_allergens"
    __table_args__ = (
        UniqueConstraint(
            "menu_item_id", "allergen_id", name="uq_menu_item_allergens_menu_item_id_allergen_id"
        ),
        Index("ix_menu_item_allergens_allergen_id", "allergen_id"),
    )

    menu_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("menu_items.id", ondelete="CASCADE"), nullable=False
    )
    allergen_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("allergens.id", ondelete="CASCADE"), nullable=False
    )
    declaration_type: Mapped[AllergenDeclarationType] = mapped_column(
        pg_enum(AllergenDeclarationType, "allergen_declaration_type"),
        nullable=False,
        server_default=AllergenDeclarationType.CONTAINS.value,
    )
    source_type: Mapped[ProvenanceSourceType] = mapped_column(
        pg_enum(ProvenanceSourceType, "allergen_source_type"),
        nullable=False,
        server_default=ProvenanceSourceType.OFFICIAL.value,
    )

    menu_item: Mapped[MenuItem] = relationship(back_populates="allergen_links")
    allergen: Mapped[Allergen] = relationship(back_populates="menu_item_links")


class DietaryTag(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A normalized dietary tag (vegan, halal, gluten_free, ...)."""

    __tablename__ = "dietary_tags"
    __table_args__ = (UniqueConstraint("normalized_name", name="uq_dietary_tags_normalized_name"),)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(100), nullable=False)

    menu_item_links: Mapped[list[MenuItemDietaryTag]] = relationship(
        back_populates="dietary_tag", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<DietaryTag name={self.name!r}>"


class MenuItemDietaryTag(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A dietary tag applied to a menu item, with provenance and confidence."""

    __tablename__ = "menu_item_dietary_tags"
    __table_args__ = (
        UniqueConstraint(
            "menu_item_id",
            "dietary_tag_id",
            name="uq_menu_item_dietary_tags_menu_item_id_dietary_tag_id",
        ),
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="confidence_range",
        ),
        Index("ix_menu_item_dietary_tags_dietary_tag_id", "dietary_tag_id"),
    )

    menu_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("menu_items.id", ondelete="CASCADE"), nullable=False
    )
    dietary_tag_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("dietary_tags.id", ondelete="CASCADE"), nullable=False
    )
    source_type: Mapped[ProvenanceSourceType] = mapped_column(
        pg_enum(ProvenanceSourceType, "dietary_tag_source_type"),
        nullable=False,
        server_default=ProvenanceSourceType.OFFICIAL.value,
    )
    #: 0.0-1.0 confidence; distinguishes official tags from inferred ones.
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)

    menu_item: Mapped[MenuItem] = relationship(back_populates="dietary_tag_links")
    dietary_tag: Mapped[DietaryTag] = relationship(back_populates="menu_item_links")
