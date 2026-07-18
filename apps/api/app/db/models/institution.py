"""Institution model -- the top-level tenant of the PlateWise schema.

An institution owns two independent branches: the menu-item catalog
(what foods exist) and the venue/station service hierarchy (where and when
food is served). Everything else in the schema hangs off an institution.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.enums import InstitutionType, pg_enum
from app.db.mixins import SourceTrackingMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.catalog import Ingredient, MenuItem
    from app.db.models.imports import DataImport
    from app.db.models.location import Venue
    from app.db.models.reports import MenuItemSuggestion


class Institution(UUIDPrimaryKeyMixin, TimestampMixin, SourceTrackingMixin, Base):
    """A university, hospital, corporate campus, or similar organization."""

    __tablename__ = "institutions"
    __table_args__ = (UniqueConstraint("slug", name="uq_institutions_slug"),)

    #: Human-readable display name, e.g. "University of Georgia".
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    #: URL-safe stable identifier, unique across PlateWise.
    slug: Mapped[str] = mapped_column(String(150), nullable=False)
    #: Category of organization (drives defaults and future behavior).
    institution_type: Mapped[InstitutionType] = mapped_column(
        pg_enum(InstitutionType, "institution_type"),
        nullable=False,
        server_default=InstitutionType.OTHER.value,
    )
    #: IANA timezone name used to interpret service dates and meal windows.
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, server_default="UTC")
    #: Identifier from an external source system (FoodPro, Nutrislice, ...).
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    #: Whether the institution is currently served by PlateWise.
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    # --- Relationships -----------------------------------------------------
    venues: Mapped[list[Venue]] = relationship(
        back_populates="institution", cascade="all, delete-orphan"
    )
    menu_items: Mapped[list[MenuItem]] = relationship(
        back_populates="institution", cascade="all, delete-orphan"
    )
    ingredients: Mapped[list[Ingredient]] = relationship(
        back_populates="institution", cascade="all, delete-orphan"
    )
    data_imports: Mapped[list[DataImport]] = relationship(
        back_populates="institution", cascade="all, delete-orphan"
    )
    menu_item_suggestions: Mapped[list[MenuItemSuggestion]] = relationship(
        back_populates="institution", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Institution slug={self.slug!r} name={self.name!r}>"
