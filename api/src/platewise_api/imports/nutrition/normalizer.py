"""Source-provided nutrition normalization.

Normalizes a source's provided nutrition into PlateWise's canonical shape:
quantized ``Decimal`` nutrient values (missing stays ``None``), a preserved
serving basis, and a deterministic content hash for idempotency/versioning.

This never fabricates values -- a missing nutrient remains ``None``.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from platewise_db.constants import NUTRIENT_FIELDS
from platewise_db.decimal_utils import quantize_nutrient, quantize_serving
from platewise_db.normalizers import content_hash

from platewise_api.imports.contracts import ImportedMenuItem


@dataclass(frozen=True)
class NormalizedNutrition:
    """Canonical source-provided nutrition ready for persistence."""

    serving_size: Decimal | None
    serving_unit: str | None
    nutrients: dict[str, Decimal | None]
    source_reference: str | None
    content_hash: str


def normalize_provided_nutrition(item: ImportedMenuItem) -> NormalizedNutrition:
    """Normalize an item's source-provided nutrition.

    The serving basis falls back from the nutrition block to the menu item's own
    default serving fields when the nutrition block omits it.
    """
    provided = item.provided_nutrition
    assert provided is not None  # callers gate on provided_nutrition_is_usable

    serving_size = provided.serving_size if provided.serving_size is not None else item.serving_size
    serving_unit = provided.serving_unit or item.serving_unit

    nutrients: dict[str, Decimal | None] = {}
    for field in NUTRIENT_FIELDS:
        raw = getattr(provided.nutrients, field)
        nutrients[field] = None if raw is None else quantize_nutrient(raw)

    normalized_serving = None if serving_size is None else quantize_serving(serving_size)

    digest = content_hash(
        [
            normalized_serving,
            serving_unit,
            *(nutrients[field] for field in NUTRIENT_FIELDS),
            provided.source_reference,
        ]
    )

    return NormalizedNutrition(
        serving_size=normalized_serving,
        serving_unit=serving_unit,
        nutrients=nutrients,
        source_reference=provided.source_reference,
        content_hash=digest,
    )
