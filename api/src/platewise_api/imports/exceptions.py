"""Typed exceptions for the import pipeline.

Unsupported or malformed input produces an explicit, typed error rather than
silent behavior. The service converts these into structured ``import_errors``
rows and per-record outcomes.
"""

from __future__ import annotations


class ImportError_(Exception):
    """Base class for all import-pipeline errors.

    Named with a trailing underscore to avoid shadowing the Python builtin
    ``ImportError``.
    """


class SourceError(ImportError_):
    """A source-level failure (fetch/validation) that aborts the whole import."""


class MalformedRecordError(ImportError_):
    """A single source record is structurally invalid and cannot be processed."""

    def __init__(self, message: str, *, record_ref: str | None = None) -> None:
        super().__init__(message)
        self.record_ref = record_ref


class RecordPersistenceError(ImportError_):
    """Persisting one classified record failed; that record is rolled back."""

    def __init__(self, message: str, *, record_ref: str | None = None) -> None:
        super().__init__(message)
        self.record_ref = record_ref
