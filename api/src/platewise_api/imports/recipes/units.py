"""Supported units and portion-to-gram conversion.

Two conversion paths are supported, both exact (``Decimal``):

1. **Mass units** convert directly to grams by a fixed factor.
2. **Portion / count / volume units** (cup, medium, breast, ...) convert only
   when the resolved provider food supplies a matching portion weight
   (:mod:`platewise_api.imports.recipes.resolver`). We never guess a density or a portion
   weight.

Anything else -- an unknown unit, a missing quantity, or a vague amount such as
"to taste" -- is explicitly *unsupported* and surfaces as a typed result, never
a silent zero or an invented value.

See ``docs/supported-units.md``.
"""

from __future__ import annotations

from decimal import Decimal

from platewise_db.decimal_utils import to_decimal

# Canonical mass units -> grams per 1 unit (exact Decimal factors).
_MASS_UNITS_TO_GRAMS: dict[str, Decimal] = {
    "g": Decimal("1"),
    "gram": Decimal("1"),
    "grams": Decimal("1"),
    "kg": Decimal("1000"),
    "kilogram": Decimal("1000"),
    "kilograms": Decimal("1000"),
    "mg": Decimal("0.001"),
    "milligram": Decimal("0.001"),
    "milligrams": Decimal("0.001"),
    "oz": Decimal("28.349523125"),
    "ounce": Decimal("28.349523125"),
    "ounces": Decimal("28.349523125"),
    "lb": Decimal("453.59237"),
    "lbs": Decimal("453.59237"),
    "pound": Decimal("453.59237"),
    "pounds": Decimal("453.59237"),
}

# Common unit spellings that map to a canonical unit token. Portion/volume units
# are recognized (so we can look up a provider portion by this token) but have no
# intrinsic gram factor.
_UNIT_ALIASES: dict[str, str] = {
    "g": "g",
    "gram": "g",
    "grams": "g",
    "gm": "g",
    "kg": "kg",
    "kilogram": "kg",
    "kilograms": "kg",
    "mg": "mg",
    "milligram": "mg",
    "milligrams": "mg",
    "oz": "oz",
    "ounce": "oz",
    "ounces": "oz",
    "lb": "lb",
    "lbs": "lb",
    "pound": "lb",
    "pounds": "lb",
    "cup": "cup",
    "cups": "cup",
    "tbsp": "tbsp",
    "tablespoon": "tbsp",
    "tablespoons": "tbsp",
    "tsp": "tsp",
    "teaspoon": "tsp",
    "teaspoons": "tsp",
    "ml": "ml",
    "milliliter": "ml",
    "milliliters": "ml",
    "l": "l",
    "liter": "l",
    "liters": "l",
    "clove": "clove",
    "cloves": "clove",
    "slice": "slice",
    "slices": "slice",
    "medium": "medium",
    "large": "large",
    "small": "small",
    "breast": "breast",
    "piece": "piece",
    "pieces": "piece",
}

# Vague amount tokens that must never be guessed.
VAGUE_TOKENS: frozenset[str] = frozenset({"to taste", "as needed", "for frying", "for garnish"})


def normalize_unit(raw: str | None) -> str | None:
    """Return the canonical unit token for ``raw``, or ``None`` if unrecognized."""
    if raw is None:
        return None
    token = raw.strip().lower()
    if not token:
        return None
    return _UNIT_ALIASES.get(token)


def is_mass_unit(unit: str | None) -> bool:
    """True if ``unit`` (canonical) has a direct gram conversion."""
    return unit in _MASS_UNITS_TO_GRAMS


def is_vague(text: str | None) -> bool:
    """True if ``text`` contains a vague, unquantifiable amount."""
    if not text:
        return False
    lowered = text.strip().lower()
    return any(token in lowered for token in VAGUE_TOKENS)


def mass_to_grams(quantity: Decimal, unit: str) -> Decimal | None:
    """Convert a mass ``quantity``/``unit`` to grams, or ``None`` if not mass.

    The result is exact and is **not** rounded here; the caller quantizes at the
    persistence boundary.
    """
    factor = _MASS_UNITS_TO_GRAMS.get(unit)
    if factor is None:
        return None
    return to_decimal(quantity) * factor
