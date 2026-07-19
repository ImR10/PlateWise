"""Dining-data source boundary.

A source adapter fetches/reads provider-specific data and returns source-neutral
contracts plus the preserved raw payload. Per-record parse failures are isolated
here (as ``MenuItemParseError``) so one malformed record never aborts the whole
import. Source-specific structures must not leak past this boundary.

This is separate from the *ingredient-nutrition provider* boundary
(:mod:`app.imports.nutrition.provider`).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from app.db.enums import ImportSourceType
from app.imports.contracts import (
    ImportedInstitution,
    ImportedMenuItem,
    ImportedStation,
    ImportedVenue,
)


@dataclass(frozen=True)
class MenuItemParseOk:
    """A successfully parsed menu-item record."""

    item: ImportedMenuItem


@dataclass(frozen=True)
class MenuItemParseError:
    """A malformed menu-item record to be logged and skipped."""

    record_ref: str
    message: str
    raw: object | None = None


MenuItemParseResult = MenuItemParseOk | MenuItemParseError


@dataclass(frozen=True)
class FetchResult:
    """The outcome of fetching from a dining source."""

    institution: ImportedInstitution
    raw_payload: dict[str, object] | None = None
    venues: tuple[ImportedVenue, ...] = ()
    stations: tuple[ImportedStation, ...] = ()
    menu_items: tuple[MenuItemParseResult, ...] = ()
    #: Requested scope echoed back for the import-run record.
    requested_scope: dict[str, object] | None = None
    warnings: tuple[str, ...] = field(default_factory=tuple)


@runtime_checkable
class DiningSource(Protocol):
    """Synchronous dining-data source adapter."""

    @property
    def source_type(self) -> ImportSourceType: ...

    @property
    def source_name(self) -> str: ...

    def fetch(self) -> FetchResult:
        """Fetch source data and return source-neutral contracts + raw payload."""
