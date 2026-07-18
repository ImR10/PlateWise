"""Import-tracking model.

Every ingestion run (fixture load, JSON/CSV import, source export) gets a
``DataImport`` record. It captures provenance, per-run counts, and an optional
raw payload so imports can be audited and made idempotent, and so catalog and
offering rows can be traced back to the run that created or last touched them.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.enums import ImportSourceType, ImportStatus, pg_enum
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.catalog import MenuItem
    from app.db.models.institution import Institution
    from app.db.models.menu import MenuOffering


class DataImport(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A single data-ingestion run and its outcome."""

    __tablename__ = "data_imports"
    __table_args__ = (
        Index("ix_data_imports_institution_id_started_at", "institution_id", "started_at"),
    )

    institution_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False
    )

    source_type: Mapped[ImportSourceType] = mapped_column(
        pg_enum(ImportSourceType, "import_source_type"), nullable=False
    )
    source_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_filename: Mapped[str | None] = mapped_column(String(500), nullable=True)
    #: The source system's snapshot timestamp for this payload, if provided.
    source_snapshot_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    status: Mapped[ImportStatus] = mapped_column(
        pg_enum(ImportStatus, "import_status"),
        nullable=False,
        server_default=ImportStatus.PENDING.value,
    )

    records_received: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    records_created: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    records_updated: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    records_unchanged: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    records_failed: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    #: Reference to the original payload in object storage (if externalized).
    raw_payload_reference: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    #: Optional inline raw payload, preserved for debugging. Supplements -- does
    #: not replace -- the normalized relational tables.
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    # --- Relationships -----------------------------------------------------
    institution: Mapped[Institution] = relationship(back_populates="data_imports")
    #: Records this import created (traceability). Matches
    #: ``MenuItem.created_by_import_id`` / ``MenuOffering.created_by_import_id``.
    created_menu_items: Mapped[list[MenuItem]] = relationship(
        back_populates="created_by_import",
        foreign_keys="MenuItem.created_by_import_id",
    )
    created_offerings: Mapped[list[MenuOffering]] = relationship(
        back_populates="created_by_import",
        foreign_keys="MenuOffering.created_by_import_id",
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<DataImport source_type={self.source_type!r} status={self.status!r}>"
