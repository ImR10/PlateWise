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
import json
from typing import Any

from platewise_db.enums import ImportSourceType
from pydantic import ValidationError

from platewise_api.imports.contracts import (
    ImportedInstitution,
    ImportedMenuItem,
    ImportedStation,
    ImportedVenue,
)
from platewise_api.imports.exceptions import SourceError
from platewise_api.imports.sources.base import (
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
        _validate_payload_envelope(self._payload)
        raw = copy.deepcopy(self._payload)

        institution_raw = raw.get("institution")
        if not isinstance(institution_raw, dict):
            raise SourceError("fixture payload missing 'institution' object")
        try:
            institution = ImportedInstitution.model_validate(institution_raw)
            venues = tuple(ImportedVenue.model_validate(v) for v in (raw.get("venues") or []))
            stations = tuple(ImportedStation.model_validate(s) for s in (raw.get("stations") or []))
        except ValidationError as exc:
            raise SourceError(f"malformed source hierarchy: {exc}") from exc

        for record in (*venues, *stations):
            if record.source_system != institution.source_system:
                raise SourceError("source hierarchy contains a conflicting source_system")

        menu_items: list[MenuItemParseResult] = []
        seen_identities: set[tuple[str, str]] = set()
        for index, record in enumerate(raw.get("menu_items") or []):
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
                identity = (
                    (item.source_system, item.external_id) if item.external_id is not None else None
                )
                identity_conflict = item.source_system != institution.source_system
                recipe_conflict = (
                    item.recipe is not None
                    and item.recipe.source_system != institution.source_system
                )
                if identity_conflict or recipe_conflict:
                    menu_items.append(
                        MenuItemParseError(
                            record_ref=record_ref,
                            message="record contains a conflicting source_system",
                        )
                    )
                elif identity is not None and identity in seen_identities:
                    menu_items.append(
                        MenuItemParseError(
                            record_ref=record_ref,
                            message="duplicate source identity within payload",
                        )
                    )
                else:
                    if identity is not None:
                        seen_identities.add(identity)
                    menu_items.append(MenuItemParseOk(item=item))

        warnings = ()
        if not menu_items and self._requested_scope is None:
            warnings = ("suspiciously_empty_payload",)

        return FetchResult(
            institution=institution,
            raw_payload=raw,
            venues=venues,
            stations=stations,
            menu_items=tuple(menu_items),
            requested_scope=self._requested_scope,
            warnings=warnings,
        )


MAX_PAYLOAD_BYTES = 5_000_000
MAX_JSON_DEPTH = 30
MAX_HIERARCHY_RECORDS = 5_000
MAX_MENU_ITEMS = 10_000


def _validate_payload_envelope(payload: dict[str, Any]) -> None:
    """Reject malformed or disproportionate fixture envelopes before copying them."""
    for key, limit in (
        ("venues", MAX_HIERARCHY_RECORDS),
        ("stations", MAX_HIERARCHY_RECORDS),
        ("menu_items", MAX_MENU_ITEMS),
    ):
        value = payload.get(key, [])
        if value is None:
            value = []
        if not isinstance(value, list):
            raise SourceError(f"fixture payload field {key!r} must be a list")
        if len(value) > limit:
            raise SourceError(f"fixture payload field {key!r} exceeds the record limit")

    try:
        encoded = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        raise SourceError("fixture payload must be valid JSON data") from exc
    if len(encoded.encode("utf-8")) > MAX_PAYLOAD_BYTES:
        raise SourceError("fixture payload exceeds the byte-size limit")

    stack: list[tuple[object, int]] = [(payload, 1)]
    while stack:
        value, depth = stack.pop()
        if depth > MAX_JSON_DEPTH:
            raise SourceError("fixture payload exceeds the JSON depth limit")
        if isinstance(value, dict):
            stack.extend((child, depth + 1) for child in value.values())
        elif isinstance(value, list):
            stack.extend((child, depth + 1) for child in value)


def _summarize_validation_error(exc: ValidationError) -> str:
    errors = exc.errors()
    if not errors:  # pragma: no cover - defensive
        return "validation error"
    first = errors[0]
    location = ".".join(str(part) for part in first.get("loc", ()))
    return f"{location}: {first.get('msg', 'invalid')}"
