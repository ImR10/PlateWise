"""Deterministic fixture dining source.

Reads a plain ``dict`` payload (the "raw" source data) and validates it into
source-neutral contracts. The institution/venue/station skeleton is validated
strictly (a structural failure is a source-level error), while each menu-item
record is validated individually so a single malformed record becomes a
``MenuItemParseError`` rather than aborting the import.

This is the only source shipped in the MVP; it is sufficient to exercise both
import paths end to end.
"""

from __future__ import annotations

import copy
from typing import Any

from pydantic import ValidationError

from app.db.enums import ImportSourceType
from app.imports.contracts import (
    ImportedInstitution,
    ImportedMenuItem,
    ImportedStation,
    ImportedVenue,
)
from app.imports.exceptions import SourceError
from app.imports.sources.base import (
    FetchResult,
    MenuItemParseError,
    MenuItemParseOk,
    MenuItemParseResult,
)


class FixtureDiningSource:
    """A ``DiningSource`` backed by an in-memory dict payload."""

    def __init__(
        self,
        payload: dict[str, Any],
        *,
        source_name: str = "fixture",
        requested_scope: dict[str, Any] | None = None,
    ) -> None:
        self._payload = payload
        self._source_name = source_name
        self._requested_scope = requested_scope

    @property
    def source_type(self) -> ImportSourceType:
        return ImportSourceType.FIXTURE

    @property
    def source_name(self) -> str:
        return self._source_name

    def fetch(self) -> FetchResult:
        raw = copy.deepcopy(self._payload)

        institution_raw = raw.get("institution")
        if not isinstance(institution_raw, dict):
            raise SourceError("fixture payload missing 'institution' object")
        try:
            institution = ImportedInstitution.model_validate(institution_raw)
            venues = tuple(
                ImportedVenue.model_validate(v) for v in raw.get("venues", []) or []
            )
            stations = tuple(
                ImportedStation.model_validate(s) for s in raw.get("stations", []) or []
            )
        except ValidationError as exc:
            raise SourceError(f"malformed source hierarchy: {exc}") from exc

        menu_items: list[MenuItemParseResult] = []
        for index, record in enumerate(raw.get("menu_items", []) or []):
            ref = None
            if isinstance(record, dict):
                ref = record.get("external_id") or record.get("name")
            record_ref = str(ref) if ref is not None else f"index:{index}"
            try:
                item = ImportedMenuItem.model_validate(record)
            except ValidationError as exc:
                menu_items.append(
                    MenuItemParseError(
                        record_ref=record_ref,
                        message=_summarize_validation_error(exc),
                        raw=record,
                    )
                )
            else:
                menu_items.append(MenuItemParseOk(item=item))

        return FetchResult(
            institution=institution,
            raw_payload=raw,
            venues=venues,
            stations=stations,
            menu_items=tuple(menu_items),
            requested_scope=self._requested_scope,
        )


def _summarize_validation_error(exc: ValidationError) -> str:
    errors = exc.errors()
    if not errors:  # pragma: no cover - defensive
        return "validation error"
    first = errors[0]
    location = ".".join(str(part) for part in first.get("loc", ()))
    return f"{location}: {first.get('msg', 'invalid')}"
