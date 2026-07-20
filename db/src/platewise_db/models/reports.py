"""Community evidence models: offering reports and menu-item suggestions.

Reports are stored as *evidence about a specific offering*, never as direct
edits to official source data. A single report must not control
recommendations; the aggregation logic (a later milestone) reads many
independent reports. Suggestions capture proposed catalog items so unverified
names never pollute the permanent catalog.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from platewise_db.base import Base
from platewise_db.enums import (
    ModerationStatus,
    ReportType,
    SuggestionStatus,
    pg_enum,
)
from platewise_db.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from platewise_db.models.catalog import MenuItem
    from platewise_db.models.institution import Institution
    from platewise_db.models.location import Station
    from platewise_db.models.menu import MenuOffering


class OfferingReport(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A community observation about one specific offering."""

    __tablename__ = "offering_reports"
    __table_args__ = (
        # One active report per reporter, per offering, per report category.
        # Retracted/rejected/etc. rows are excluded so a reporter can supersede
        # their own earlier report.
        Index(
            "uq_offering_reports_active_reporter_category",
            "offering_id",
            "reporter_id",
            "report_type",
            unique=True,
            postgresql_where=text("moderation_status = 'active'"),
        ),
        Index("ix_offering_reports_offering_id_reported_at", "offering_id", "reported_at"),
        Index("ix_offering_reports_reporter_id_offering_id", "reporter_id", "offering_id"),
    )

    offering_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("menu_offerings.id", ondelete="CASCADE"), nullable=False
    )
    #: Privacy-preserving reporter identity (installation id, user id, ...).
    #: Not a foreign key -- the MVP has no users table and never exposes this.
    reporter_id: Mapped[str] = mapped_column(String(255), nullable=False)

    report_type: Mapped[ReportType] = mapped_column(
        pg_enum(ReportType, "report_type"), nullable=False
    )
    #: For ``replacement`` reports: the catalog item observed in place of the
    #: offered one. Points at an existing catalog item (or NULL).
    replacement_menu_item_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("menu_items.id", ondelete="SET NULL"), nullable=True
    )

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    #: Server-generated/validated observation time.
    reported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    retracted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    moderation_status: Mapped[ModerationStatus] = mapped_column(
        pg_enum(ModerationStatus, "moderation_status"),
        nullable=False,
        server_default=ModerationStatus.ACTIVE.value,
    )

    # --- Relationships -----------------------------------------------------
    offering: Mapped[MenuOffering] = relationship(back_populates="reports")
    replacement_menu_item: Mapped[MenuItem | None] = relationship(
        foreign_keys=[replacement_menu_item_id]
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<OfferingReport type={self.report_type!r} status={self.moderation_status!r}>"


class MenuItemSuggestion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A proposed menu item awaiting verification before it enters the catalog."""

    __tablename__ = "menu_item_suggestions"
    __table_args__ = (
        Index("ix_menu_item_suggestions_institution_id_status", "institution_id", "status"),
    )

    institution_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False
    )
    station_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("stations.id", ondelete="SET NULL"), nullable=True
    )
    related_offering_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("menu_offerings.id", ondelete="SET NULL"), nullable=True
    )

    proposed_name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    #: Privacy-preserving identity of the submitter.
    submitted_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    status: Mapped[SuggestionStatus] = mapped_column(
        pg_enum(SuggestionStatus, "suggestion_status"),
        nullable=False,
        server_default=SuggestionStatus.PENDING.value,
    )
    #: Set once the suggestion is matched/approved to a catalog item.
    matched_menu_item_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("menu_items.id", ondelete="SET NULL"), nullable=True
    )

    # --- Relationships -----------------------------------------------------
    institution: Mapped[Institution] = relationship(back_populates="menu_item_suggestions")
    station: Mapped[Station | None] = relationship(foreign_keys=[station_id])
    related_offering: Mapped[MenuOffering | None] = relationship(foreign_keys=[related_offering_id])
    matched_menu_item: Mapped[MenuItem | None] = relationship(foreign_keys=[matched_menu_item_id])

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<MenuItemSuggestion name={self.proposed_name!r} status={self.status!r}>"
