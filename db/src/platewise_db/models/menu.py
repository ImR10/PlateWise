"""Menu offerings -- the placement of a catalog item at a station and time.

An offering is *not* the food itself. It is a scheduled/live record that
answers "where and when is this item served?" and points at a catalog
``MenuItem`` through ``menu_item_id``. The same catalog item may back many
offerings across venues, stations, dates, and meal periods without being
duplicated.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from platewise_db.base import Base
from platewise_db.enums import ImportSourceType, MealPeriod, OfferingStatus, pg_enum
from platewise_db.mixins import SourceTrackingMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from platewise_db.models.catalog import MenuItem
    from platewise_db.models.imports import DataImport
    from platewise_db.models.location import Station
    from platewise_db.models.reports import OfferingReport

#: Marker for rows whose external origin is unknown (hand-created or pre-import).
UNKNOWN_SOURCE_SYSTEM = "unknown"


class MenuOffering(UUIDPrimaryKeyMixin, TimestampMixin, SourceTrackingMixin, Base):
    """A menu item's placement at a specific station, date, and meal period."""

    __tablename__ = "menu_offerings"
    __table_args__ = (
        # Prevent duplicate offerings for the same slot. ``starts_at`` is part
        # of the key; NULLS NOT DISTINCT (PostgreSQL 15+) makes rows with a
        # NULL start time still collide so re-imports stay idempotent.
        UniqueConstraint(
            "station_id",
            "menu_item_id",
            "service_date",
            "meal_period",
            "starts_at",
            name="uq_menu_offerings_slot",
            postgresql_nulls_not_distinct=True,
        ),
        Index(
            "ix_menu_offerings_station_id_service_date_meal_period",
            "station_id",
            "service_date",
            "meal_period",
        ),
        Index("ix_menu_offerings_menu_item_id_service_date", "menu_item_id", "service_date"),
        # External identity for idempotent offering upserts (station-scoped).
        Index(
            "uq_menu_offerings_station_id_source_system_external_id",
            "station_id",
            "source_system",
            "external_id",
            unique=True,
            postgresql_where=text("external_id IS NOT NULL"),
        ),
    )

    station_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("stations.id", ondelete="CASCADE"), nullable=False
    )
    source_system: Mapped[str] = mapped_column(
        String(100), nullable=False, server_default=UNKNOWN_SOURCE_SYSTEM
    )
    #: Pointer into the institution-owned catalog. RESTRICT protects catalog
    #: items from deletion while offerings still reference them.
    menu_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("menu_items.id", ondelete="RESTRICT"), nullable=False
    )

    service_date: Mapped[date] = mapped_column(Date, nullable=False)
    meal_period: Mapped[MealPeriod] = mapped_column(
        pg_enum(MealPeriod, "meal_period"), nullable=False
    )

    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    #: Official status from the source; never overwritten by community reports.
    official_status: Mapped[OfferingStatus] = mapped_column(
        pg_enum(OfferingStatus, "offering_status"),
        nullable=False,
        server_default=OfferingStatus.SCHEDULED.value,
    )
    source_type: Mapped[ImportSourceType | None] = mapped_column(
        pg_enum(ImportSourceType, "offering_source_type"), nullable=True
    )
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_by_import_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("data_imports.id", ondelete="SET NULL"), nullable=True
    )
    updated_by_import_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("data_imports.id", ondelete="SET NULL"), nullable=True
    )

    # --- Relationships -----------------------------------------------------
    station: Mapped[Station] = relationship(back_populates="offerings")
    menu_item: Mapped[MenuItem] = relationship(
        back_populates="offerings", foreign_keys=[menu_item_id]
    )
    reports: Mapped[list[OfferingReport]] = relationship(
        back_populates="offering", cascade="all, delete-orphan"
    )
    created_by_import: Mapped[DataImport | None] = relationship(
        back_populates="created_offerings", foreign_keys=[created_by_import_id]
    )
    updated_by_import: Mapped[DataImport | None] = relationship(foreign_keys=[updated_by_import_id])

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<MenuOffering service_date={self.service_date!r} meal_period={self.meal_period!r}>"
