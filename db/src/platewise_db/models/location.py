"""Service-hierarchy models: venues and the stations inside them.

    Institution -> Venue -> Station -> (Menu Offering)

Venues and stations describe *where* food is served. They are intentionally
kept separate from the menu-item catalog (what the food is). Neither is
auto-deleted when it disappears from a source import; prefer ``is_active =
False`` over deletion.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, String, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from platewise_db.base import Base
from platewise_db.enums import VenueType, pg_enum
from platewise_db.mixins import SourceTrackingMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from platewise_db.models.institution import Institution
    from platewise_db.models.menu import MenuOffering

#: Marker for rows whose external origin is unknown (hand-created or pre-import).
UNKNOWN_SOURCE_SYSTEM = "unknown"


class Venue(UUIDPrimaryKeyMixin, TimestampMixin, SourceTrackingMixin, Base):
    """A physical place where food is served (dining hall, cafe, ...)."""

    __tablename__ = "venues"
    __table_args__ = (
        UniqueConstraint("institution_id", "slug", name="uq_venues_institution_id_slug"),
        Index(
            "uq_venues_institution_id_source_system_external_id",
            "institution_id",
            "source_system",
            "external_id",
            unique=True,
            postgresql_where=text("external_id IS NOT NULL"),
        ),
    )

    institution_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_system: Mapped[str] = mapped_column(
        String(100), nullable=False, server_default=UNKNOWN_SOURCE_SYSTEM
    )
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    #: URL-safe identifier, unique within the owning institution.
    slug: Mapped[str] = mapped_column(String(150), nullable=False)
    venue_type: Mapped[VenueType] = mapped_column(
        pg_enum(VenueType, "venue_type"),
        nullable=False,
        server_default=VenueType.OTHER.value,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    # --- Relationships -----------------------------------------------------
    institution: Mapped[Institution] = relationship(back_populates="venues")
    stations: Mapped[list[Station]] = relationship(
        back_populates="venue", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Venue slug={self.slug!r} name={self.name!r}>"


class Station(UUIDPrimaryKeyMixin, TimestampMixin, SourceTrackingMixin, Base):
    """An individual serving area inside a venue (Grill, Salad Bar, ...)."""

    __tablename__ = "stations"
    __table_args__ = (
        UniqueConstraint("venue_id", "slug", name="uq_stations_venue_id_slug"),
        Index(
            "uq_stations_venue_id_source_system_external_id",
            "venue_id",
            "source_system",
            "external_id",
            unique=True,
            postgresql_where=text("external_id IS NOT NULL"),
        ),
    )

    venue_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("venues.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_system: Mapped[str] = mapped_column(
        String(100), nullable=False, server_default=UNKNOWN_SOURCE_SYSTEM
    )
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    #: URL-safe identifier, unique within the owning venue.
    slug: Mapped[str] = mapped_column(String(150), nullable=False)
    #: Free-form station category (no fixed vocabulary in the source data).
    station_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    # --- Relationships -----------------------------------------------------
    venue: Mapped[Venue] = relationship(back_populates="stations")
    offerings: Mapped[list[MenuOffering]] = relationship(
        back_populates="station", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Station slug={self.slug!r} name={self.name!r}>"
