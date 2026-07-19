"""Decimal precision and rounding policy for the import pipeline.

All quantity, gram, and nutrient arithmetic uses :class:`decimal.Decimal` so
results are exact and deterministic (never binary floating point). Intermediate
calculations are **not** rounded; rounding happens only at defined persistence /
output boundaries via the ``quantize_*`` helpers below.

Policy
------
* Rounding mode: ``ROUND_HALF_UP`` everywhere.
* Nutrient values persist at 2 decimal places (``Numeric(10, 2)``).
* Gram weights and parsed/normalized quantities persist at 4 decimal places
  (``Numeric(12, 4)``).
* Serving sizes persist at 3 decimal places (``Numeric(10, 3)``).

Equality in tests is checked by comparing quantized ``Decimal`` values, not
floats.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

ROUNDING = ROUND_HALF_UP

NUTRIENT_EXP = Decimal("0.01")  # 2 dp -> Numeric(10, 2)
GRAMS_EXP = Decimal("0.0001")  # 4 dp -> Numeric(12, 4)
QUANTITY_EXP = Decimal("0.0001")  # 4 dp -> Numeric(12, 4)
SERVING_EXP = Decimal("0.001")  # 3 dp -> Numeric(10, 3)

HUNDRED = Decimal("100")


def to_decimal(value: object) -> Decimal:
    """Coerce ``int``/``str``/``Decimal`` to ``Decimal`` losslessly.

    ``float`` is intentionally routed through ``str`` so that a value like
    ``0.1`` becomes ``Decimal("0.1")`` rather than its binary expansion.
    """
    if isinstance(value, Decimal):
        return value
    if isinstance(value, float):
        return Decimal(str(value))
    return Decimal(value)  # type: ignore[arg-type]


def quantize_nutrient(value: Decimal) -> Decimal:
    return value.quantize(NUTRIENT_EXP, rounding=ROUNDING)


def quantize_grams(value: Decimal) -> Decimal:
    return value.quantize(GRAMS_EXP, rounding=ROUNDING)


def quantize_quantity(value: Decimal) -> Decimal:
    return value.quantize(QUANTITY_EXP, rounding=ROUNDING)


def quantize_serving(value: Decimal) -> Decimal:
    return value.quantize(SERVING_EXP, rounding=ROUNDING)
