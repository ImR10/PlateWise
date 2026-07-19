"""Shared normalization helpers: names and deterministic content hashes.

Content hashes drive idempotency and change detection: re-importing identical
source data yields identical hashes, so no new rows are created.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable


def normalize_name(value: str) -> str:
    """Return a search/match-friendly normalized form of a display name."""
    return " ".join(value.strip().lower().split())


def content_hash(parts: Iterable[object]) -> str:
    """Deterministic SHA-256 hex digest over ``parts``.

    ``None`` is encoded distinctly from an empty string so that a missing value
    and a blank value hash differently. Order is significant.
    """
    hasher = hashlib.sha256()
    for part in parts:
        token = "\x00NULL\x00" if part is None else str(part)
        hasher.update(token.encode("utf-8"))
        hasher.update(b"\x1f")  # unit separator between fields
    return hasher.hexdigest()
