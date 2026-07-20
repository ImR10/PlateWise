"""Structured recipe ingredient-line parsing.

Each :class:`~platewise_api.imports.contracts.ImportedRecipeIngredient` is turned into a
:class:`ParsedIngredient`. When the source already provides structured fields
(quantity/unit/name), those are used and only normalized. When only
``original_text`` is present, a conservative parse extracts a leading quantity
(integer, decimal, or simple fraction), a recognized unit token, and the
remaining name plus any preparation note.

The parser never invents a quantity: an unparseable or absent amount stays
``None`` and is flagged, not guessed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from platewise_db.decimal_utils import to_decimal
from platewise_db.enums import RawOrCooked
from platewise_db.normalizers import normalize_name

from platewise_api.imports.contracts import ImportedRecipeIngredient
from platewise_api.imports.recipes.units import is_vague, normalize_unit

# "1", "1.5", "1/2", "1 1/2" at the start of a line.
_QUANTITY_RE = re.compile(r"^\s*(\d+\s+\d+/\d+|\d+/\d+|\d+(?:\.\d+)?)\s*(.*)$")
_FIRST_TOKEN_RE = re.compile(r"^\s*(\S+)\s*(.*)$")


@dataclass(frozen=True)
class ParsedIngredient:
    """A parsed, normalized recipe ingredient line."""

    line_no: int
    original_text: str
    quantity: Decimal | None
    unit: str | None  # canonical unit token, or None
    raw_unit: str | None  # the unit token as written (for provider portion match)
    name: str | None
    normalized_name: str | None
    preparation: str | None
    is_optional: bool
    raw_or_cooked: RawOrCooked | None
    external_food_id: str | None
    is_vague: bool


def _parse_quantity(token: str) -> Decimal | None:
    token = token.strip()
    try:
        if " " in token:  # mixed number "1 1/2"
            whole, frac = token.split(" ", 1)
            num, den = frac.split("/")
            return to_decimal(whole) + (to_decimal(num) / to_decimal(den))
        if "/" in token:  # simple fraction "1/2"
            num, den = token.split("/")
            return to_decimal(num) / to_decimal(den)
        return to_decimal(token)
    except (InvalidOperation, ZeroDivisionError, ValueError):
        return None


def _detect_raw_or_cooked(text: str) -> RawOrCooked | None:
    lowered = text.lower()
    if "cooked" in lowered:
        return RawOrCooked.COOKED
    if "raw" in lowered:
        return RawOrCooked.RAW
    return None


def _split_preparation(name: str) -> tuple[str, str | None]:
    """Split "tomatoes, diced" or "onion (chopped)" into (name, preparation)."""
    prep: str | None = None
    paren = re.search(r"\(([^)]*)\)", name)
    if paren:
        prep = paren.group(1).strip()
        name = (name[: paren.start()] + name[paren.end() :]).strip()
    if "," in name:
        head, tail = name.split(",", 1)
        name = head.strip()
        tail = tail.strip()
        prep = f"{prep}, {tail}" if prep else tail
    return name.strip(), (prep or None)


def parse_ingredient(imported: ImportedRecipeIngredient) -> ParsedIngredient:
    """Parse and normalize a single imported ingredient line."""
    quantity = imported.quantity
    raw_unit = imported.unit
    name = imported.name
    preparation = imported.preparation

    if quantity is None and (name is None or raw_unit is None):
        # Only free text is available -- parse it conservatively.
        text = imported.original_text.strip()
        match = _QUANTITY_RE.match(text)
        if match:
            quantity = _parse_quantity(match.group(1))
            remainder = match.group(2)
        else:
            remainder = text
        if raw_unit is None and remainder:
            token_match = _FIRST_TOKEN_RE.match(remainder)
            if token_match and normalize_unit(token_match.group(1)) is not None:
                raw_unit = token_match.group(1)
                remainder = token_match.group(2)
        if name is None:
            name = remainder or None

    if name is not None:
        name, extra_prep = _split_preparation(name)
        if extra_prep and not preparation:
            preparation = extra_prep

    normalized = normalize_name(name) if name else None

    return ParsedIngredient(
        line_no=imported.line_no,
        original_text=imported.original_text,
        quantity=quantity,
        unit=normalize_unit(raw_unit),
        raw_unit=raw_unit,
        name=name,
        normalized_name=normalized,
        preparation=preparation,
        is_optional=imported.is_optional,
        raw_or_cooked=_detect_raw_or_cooked(imported.original_text),
        external_food_id=imported.external_food_id,
        is_vague=is_vague(imported.original_text),
    )
