"""Import service orchestration.

Coordinates the full import workflow and owns the transaction boundary:

1. ``source.fetch()`` runs first (validation + raw-payload preservation).
2. The institution is upserted and a ``DataImport`` run row is created.
3. Hierarchy (venues, stations) is upserted.
4. Each menu-item record is processed inside its **own savepoint**, so a single
   record's failure rolls back only that record's writes while the run and its
   structured errors persist. Malformed/invalid records are logged and skipped.
5. Counters and final status are written to the run.

Safety guarantees:

* The importer only upserts; it never deletes. An empty or suspicious source
  response is therefore inherently non-destructive (existing data is untouched).
* Source-provided and recipe-calculated nutrition coexist; neither overwrites
  the other.
* Missing nutrients stay ``NULL``; unresolved ingredients contribute nothing and
  never zero; incomplete calculated nutrition is flagged, not trusted.
"""

from __future__ import annotations

import hashlib
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from time import perf_counter
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.enums import (
    ImportErrorSeverity,
    ImportErrorStage,
    ImportStatus,
    IngredientResolutionStatus,
)
from app.db.models import DataImport, DataImportError, Institution, Station
from app.imports import repositories as repo
from app.imports.classifiers import classify, provided_nutrition_is_usable
from app.imports.contracts import ImportedMenuItem
from app.imports.enums import RecordClassification
from app.imports.nutrition.normalizer import normalize_provided_nutrition
from app.imports.nutrition.provider import (
    CachingIngredientNutritionProvider,
    IngredientNutritionProvider,
)
from app.imports.provenance import is_large_discrepancy
from app.imports.recipes.calculator import calculate_recipe_nutrition
from app.imports.recipes.parser import parse_ingredient
from app.imports.recipes.resolver import resolve_ingredient
from app.imports.sources.base import DiningSource, MenuItemParseError, MenuItemParseOk

_NON_CONTRIBUTING = frozenset(
    {IngredientResolutionStatus.RESOLVED, IngredientResolutionStatus.EXCLUDED_NON_NUTRITIVE}
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ImportCounters:
    """Caller-visible immutable import counters."""

    created: int = 0
    updated: int = 0
    unchanged: int = 0
    skipped: int = 0
    failed: int = 0
    ingredients_resolved: int = 0
    ingredients_unresolved: int = 0
    nutrition_provided: int = 0
    nutrition_calculated: int = 0


@dataclass
class _Counters:
    created: int = 0
    updated: int = 0
    unchanged: int = 0
    skipped: int = 0
    failed: int = 0
    ingredients_resolved: int = 0
    ingredients_unresolved: int = 0
    nutrition_provided: int = 0
    nutrition_calculated: int = 0

    def add(self, other: _Counters) -> None:
        self.created += other.created
        self.updated += other.updated
        self.unchanged += other.unchanged
        self.ingredients_resolved += other.ingredients_resolved
        self.ingredients_unresolved += other.ingredients_unresolved
        self.nutrition_provided += other.nutrition_provided
        self.nutrition_calculated += other.nutrition_calculated

    def snapshot(self) -> ImportCounters:
        return ImportCounters(**self.__dict__)


@dataclass
class ImportResult:
    """Summary of an import run."""

    import_id: UUID
    status: ImportStatus
    counters: ImportCounters
    classification: dict[RecordClassification, int] = field(default_factory=dict)
    error_count: int = 0
    warning_count: int = 0


def _now() -> datetime:
    return datetime.now(UTC)


def _safe_record_ref(external_id: str | None, name: str | None = None) -> str:
    if external_id:
        return external_id[:255]
    digest = hashlib.sha256((name or "unknown").encode("utf-8")).hexdigest()[:16]
    return f"record:{digest}"


def run_import(
    session: Session,
    source: DiningSource,
    provider: IngredientNutritionProvider,
    *,
    tolerant: bool = True,
) -> ImportResult:
    """Execute an import from ``source`` using ``provider`` for recipe nutrition."""
    started_at = _now()
    started_clock = perf_counter()
    try:
        fetched = source.fetch()
    except Exception as exc:
        logger.error(
            "import_run_fetch_failed",
            extra={
                "source_type": source.source_type.value,
                "source_name": source.source_name,
                "stage": ImportErrorStage.FETCH.value,
                "exception_type": type(exc).__name__,
            },
        )
        raise

    logger.info(
        "import_run_started",
        extra={
            "source_type": source.source_type.value,
            "source_name": source.source_name,
            "source_system": fetched.institution.source_system,
            "institution_ref": _safe_record_ref(
                fetched.institution.external_id, fetched.institution.name
            ),
            "requested_scope_keys": sorted((fetched.requested_scope or {}).keys()),
            "total_record_count": len(fetched.menu_items),
        },
    )

    provider = CachingIngredientNutritionProvider(provider)
    run_scope = session.begin_nested()
    counters = _Counters()
    classification_counts: dict[RecordClassification, int] = defaultdict(int)
    fatal_error: tuple[ImportErrorStage, str, str] | None = None

    try:
        institution, _ = repo.upsert_institution(session, fetched.institution)
        run = _new_run(session, source, fetched, institution, started_at)

        for warning_code in fetched.warnings:
            repo.record_error(
                session,
                run,
                severity=ImportErrorSeverity.WARNING,
                stage=ImportErrorStage.VALIDATE,
                code=warning_code[:100],
                message="source adapter reported a review warning",
            )

        venue_by_key: dict[str, object] = {}
        for imported_venue in fetched.venues:
            venue, _ = repo.upsert_venue(session, institution, imported_venue)
            if imported_venue.external_id:
                venue_by_key[imported_venue.external_id] = venue
            venue_by_key[imported_venue.slug] = venue

        station_by_key: dict[str, Station] = {}
        for imported_station in fetched.stations:
            parent = venue_by_key.get(imported_station.venue_external_id or "") or venue_by_key.get(
                imported_station.venue_slug or ""
            )
            if parent is None:
                repo.record_error(
                    session,
                    run,
                    severity=ImportErrorSeverity.WARNING,
                    stage=ImportErrorStage.NORMALIZE,
                    code="station_without_venue",
                    message="station references an unknown venue",
                    source_record_ref=_safe_record_ref(
                        imported_station.external_id, imported_station.slug
                    ),
                )
                continue
            station, _ = repo.upsert_station(
                session, parent, imported_station  # type: ignore[arg-type]
            )
            if imported_station.external_id:
                station_by_key[imported_station.external_id] = station
            station_by_key[imported_station.slug] = station

        for result in fetched.menu_items:
            if isinstance(result, MenuItemParseError):
                repo.record_error(
                    session,
                    run,
                    severity=ImportErrorSeverity.ERROR,
                    stage=ImportErrorStage.VALIDATE,
                    code="malformed_record",
                    message=result.message[:1000],
                    source_record_ref=result.record_ref[:255],
                )
                counters.failed += 1
                counters.skipped += 1
                classification_counts[RecordClassification.INVALID] += 1
                if not tolerant:
                    fatal_error = (
                        ImportErrorStage.VALIDATE,
                        "malformed_record",
                        result.record_ref[:255],
                    )
                    break
                continue

            assert isinstance(result, MenuItemParseOk)
            item = result.item
            classification = classify(item)
            classification_counts[classification] += 1
            record_ref = _safe_record_ref(item.external_id, item.name)

            if classification == RecordClassification.INVALID:
                repo.record_error(
                    session,
                    run,
                    severity=ImportErrorSeverity.ERROR,
                    stage=ImportErrorStage.CLASSIFY,
                    code="invalid_record",
                    message="record is structurally unusable",
                    source_record_ref=record_ref,
                )
                counters.failed += 1
                counters.skipped += 1
                if not tolerant:
                    fatal_error = (ImportErrorStage.CLASSIFY, "invalid_record", record_ref)
                    break
                continue

            try:
                with session.begin_nested():
                    delta = _process_item(
                        session,
                        institution,
                        station_by_key,
                        provider,
                        run,
                        item,
                        classification,
                    )
            except Exception as exc:  # noqa: BLE001 - isolated and safely summarized
                repo.record_error(
                    session,
                    run,
                    severity=ImportErrorSeverity.ERROR,
                    stage=ImportErrorStage.PERSIST,
                    code="persist_failed",
                    message="record persistence failed; see server logs",
                    source_record_ref=record_ref,
                )
                logger.error(
                    "import_record_failed",
                    extra={
                        "import_id": str(run.id),
                        "stage": ImportErrorStage.PERSIST.value,
                        "error_code": "persist_failed",
                        "record_ref": record_ref,
                        "exception_type": type(exc).__name__,
                    },
                )
                counters.failed += 1
                if not tolerant:
                    fatal_error = (ImportErrorStage.PERSIST, "persist_failed", record_ref)
                    break
            else:
                counters.add(delta)

        if fatal_error is not None:
            run_scope.rollback()
            failed_counters = _Counters(failed=1, skipped=1)
            failed_run = _persist_failed_run(
                session,
                source,
                fetched,
                started_at,
                failed_counters,
                fatal_error,
            )
            duration_ms = round((perf_counter() - started_clock) * 1000, 3)
            logger.error(
                "import_run_rolled_back",
                extra={
                    "import_id": str(failed_run.id),
                    "source_system": fetched.institution.source_system,
                    "stage": fatal_error[0].value,
                    "error_code": fatal_error[1],
                    "duration_ms": duration_ms,
                },
            )
            return ImportResult(
                import_id=failed_run.id,
                status=ImportStatus.FAILED,
                counters=failed_counters.snapshot(),
                classification=dict(classification_counts),
                error_count=1,
            )

        error_count, warning_count = _issue_counts(session, run)
        _finalize_run(run, counters, error_count, warning_count)
        session.flush()
        run_scope.commit()
    except Exception:
        if run_scope.is_active:
            run_scope.rollback()
        logger.error(
            "import_run_failed",
            extra={
                "source_system": fetched.institution.source_system,
                "stage": ImportErrorStage.FINALIZE.value,
                "duration_ms": round((perf_counter() - started_clock) * 1000, 3),
            },
        )
        raise

    duration_ms = round((perf_counter() - started_clock) * 1000, 3)
    logger.info(
        "import_run_completed",
        extra={
            "import_id": str(run.id),
            "source_system": fetched.institution.source_system,
            "status": run.status.value,
            "total_record_count": len(fetched.menu_items),
            "records_created": counters.created,
            "records_updated": counters.updated,
            "records_unchanged": counters.unchanged,
            "records_skipped": counters.skipped,
            "records_failed": counters.failed,
            "ingredients_resolved": counters.ingredients_resolved,
            "ingredients_unresolved": counters.ingredients_unresolved,
            "nutrition_provided_count": counters.nutrition_provided,
            "nutrition_calculated_count": counters.nutrition_calculated,
            "warning_count": warning_count,
            "error_count": error_count,
            "duration_ms": duration_ms,
        },
    )
    return ImportResult(
        import_id=run.id,
        status=run.status,
        counters=counters.snapshot(),
        classification=dict(classification_counts),
        error_count=error_count,
        warning_count=warning_count,
    )


def _new_run(session, source, fetched, institution, started_at: datetime) -> DataImport:
    run = DataImport(
        institution_id=institution.id,
        source_type=source.source_type,
        source_name=source.source_name,
        status=ImportStatus.RUNNING,
        started_at=started_at,
        raw_payload=fetched.raw_payload,
        requested_scope=fetched.requested_scope,
        records_received=len(fetched.menu_items),
    )
    session.add(run)
    session.flush()
    return run


def _issue_counts(session: Session, run: DataImport) -> tuple[int, int]:
    def count(severity: ImportErrorSeverity) -> int:
        value = session.scalar(
            select(func.count())
            .select_from(DataImportError)
            .where(
                DataImportError.data_import_id == run.id,
                DataImportError.severity == severity,
            )
        )
        return int(value or 0)

    return count(ImportErrorSeverity.ERROR), count(ImportErrorSeverity.WARNING)


def _finalize_run(
    run: DataImport, counters: _Counters, error_count: int, warning_count: int
) -> None:
    run.records_created = counters.created
    run.records_updated = counters.updated
    run.records_unchanged = counters.unchanged
    run.records_skipped = counters.skipped
    run.records_failed = counters.failed
    run.ingredients_resolved = counters.ingredients_resolved
    run.ingredients_unresolved = counters.ingredients_unresolved
    run.nutrition_provided_count = counters.nutrition_provided
    run.nutrition_calculated_count = counters.nutrition_calculated
    run.completed_at = _now()
    run.status = (
        ImportStatus.COMPLETED_WITH_ERRORS
        if error_count or warning_count or counters.failed
        else ImportStatus.COMPLETED
    )
    if error_count or warning_count:
        run.error_summary = (
            f"{error_count} error(s), {warning_count} warning(s); see import_errors"
        )


def _persist_failed_run(
    session: Session,
    source,
    fetched,
    started_at: datetime,
    counters: _Counters,
    fatal_error: tuple[ImportErrorStage, str, str],
) -> DataImport:
    institution, _ = repo.upsert_institution(session, fetched.institution)
    run = _new_run(session, source, fetched, institution, started_at)
    run.status = ImportStatus.FAILED
    run.completed_at = _now()
    run.records_failed = counters.failed
    run.records_skipped = counters.skipped
    run.error_summary = "non-tolerant import rolled back; see import_errors"
    repo.record_error(
        session,
        run,
        severity=ImportErrorSeverity.ERROR,
        stage=fatal_error[0],
        code=fatal_error[1],
        message="non-tolerant import rolled back after a record failure",
        source_record_ref=fatal_error[2],
    )
    session.flush()
    return run


def _count_outcome(counters: _Counters, outcome: str) -> None:
    if outcome == "created":
        counters.created += 1
    elif outcome == "updated":
        counters.updated += 1
    else:
        counters.unchanged += 1


def _process_item(
    session: Session,
    institution: Institution,
    station_by_key: dict[str, Station],
    provider: IngredientNutritionProvider,
    run: DataImport,
    item: ImportedMenuItem,
    classification: RecordClassification,
) -> _Counters:
    """Persist one classified menu item and all its available nutrition paths."""
    counters = _Counters()
    menu_item, outcome = repo.upsert_menu_item(session, institution, item, run)
    _count_outcome(counters, outcome)
    record_ref = _safe_record_ref(item.external_id, item.name)

    # Offering placement (optional).
    if item.station_external_id and item.service_date and item.meal_period:
        station = station_by_key.get(item.station_external_id)
        if station is not None:
            repo.upsert_offering(session, station, menu_item, item, run)

    # Path A: source-provided nutrition.
    source_calories = None
    if provided_nutrition_is_usable(item):
        normalized = normalize_provided_nutrition(item)
        source_calories = normalized.nutrients.get("calories")
        _, n_outcome = repo.upsert_source_nutrition(session, menu_item, normalized, run)
        if n_outcome in ("created", "updated"):
            counters.nutrition_provided += 1

    # Path B: recipe-based nutrition.
    if item.recipe is not None and item.recipe.ingredients:
        version, r_outcome = repo.upsert_recipe_version(session, menu_item, item.recipe, run)
        calculated_calories = None
        if r_outcome in ("created", "updated"):
            resolved = [
                resolve_ingredient(parse_ingredient(ing), provider)
                for ing in item.recipe.ingredients
            ]
            provider_food_ids: dict[tuple[str, str], object] = {}
            for res in resolved:
                if res.provider_food is None:
                    continue
                key = (res.provider_food.provider, res.provider_food.provider_food_id)
                if key not in provider_food_ids:
                    provider_food_ids[key] = repo.upsert_provider_food(
                        session, res.provider_food
                    ).id
            repo.persist_recipe_ingredients(session, version, resolved, provider_food_ids)

            calc = calculate_recipe_nutrition(item.recipe.servings, resolved)
            calculated_calories = calc.per_serving.get("calories") if calc.is_complete else None
            _, c_outcome = repo.upsert_calculated_nutrition(session, menu_item, version, calc, run)
            if c_outcome in ("created", "updated"):
                counters.nutrition_calculated += 1

            counters.ingredients_resolved += sum(
                1 for r in resolved if r.contributes_nutrition
            )
            for res in resolved:
                if res.status not in _NON_CONTRIBUTING:
                    counters.ingredients_unresolved += 1
                    repo.record_error(
                        session,
                        run,
                        severity=ImportErrorSeverity.WARNING,
                        stage=ImportErrorStage.RESOLVE_INGREDIENT,
                        code=res.status.value,
                        message=res.error_detail or "unresolved ingredient",
                        source_record_ref=record_ref,
                        menu_item_id=menu_item.id,
                        ingredient_context=f"line:{res.parsed.line_no}",
                    )
            if not calc.is_complete:
                repo.record_error(
                    session,
                    run,
                    severity=ImportErrorSeverity.WARNING,
                    stage=ImportErrorStage.CALCULATE_NUTRITION,
                    code=calc.status.value,
                    message="; ".join(calc.reasons) or "incomplete calculated nutrition",
                    source_record_ref=record_ref,
                    menu_item_id=menu_item.id,
                )
                logger.warning(
                    "import_recipe_calculation_incomplete",
                    extra={
                        "import_id": str(run.id),
                        "source_system": item.source_system,
                        "record_ref": record_ref,
                        "stage": ImportErrorStage.CALCULATE_NUTRITION.value,
                        "error_code": calc.status.value,
                        "resolved_ingredient_count": calc.resolved_count,
                        "unresolved_ingredient_count": calc.unresolved_count,
                    },
                )
        else:
            active_calculated = repo.get_active_calculated_nutrition(session, menu_item)
            if active_calculated is not None and active_calculated.is_complete:
                calculated_calories = active_calculated.calories

        if source_calories is not None and is_large_discrepancy(
            source_calories, calculated_calories
        ):
            repo.record_error(
                session,
                run,
                severity=ImportErrorSeverity.WARNING,
                stage=ImportErrorStage.CALCULATE_NUTRITION,
                code="nutrition_discrepancy",
                message="calculated calories differ materially from source-provided",
                source_record_ref=record_ref,
                menu_item_id=menu_item.id,
            )
            logger.warning(
                "import_nutrition_discrepancy",
                extra={
                    "import_id": str(run.id),
                    "source_system": item.source_system,
                    "record_ref": record_ref,
                    "stage": ImportErrorStage.CALCULATE_NUTRITION.value,
                    "error_code": "nutrition_discrepancy",
                },
            )

    return counters
