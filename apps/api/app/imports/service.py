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

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime

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
from app.imports.nutrition.provider import IngredientNutritionProvider
from app.imports.provenance import is_large_discrepancy
from app.imports.recipes.calculator import calculate_recipe_nutrition
from app.imports.recipes.parser import parse_ingredient
from app.imports.recipes.resolver import resolve_ingredient
from app.imports.sources.base import DiningSource, MenuItemParseError, MenuItemParseOk

_NON_CONTRIBUTING = frozenset(
    {IngredientResolutionStatus.RESOLVED, IngredientResolutionStatus.EXCLUDED_NON_NUTRITIVE}
)


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


@dataclass
class ImportResult:
    """Summary of an import run."""

    import_id: object
    status: ImportStatus
    counters: _Counters
    classification: dict[RecordClassification, int] = field(default_factory=dict)
    error_count: int = 0


def _now() -> datetime:
    return datetime.now(UTC)


def run_import(
    session: Session,
    source: DiningSource,
    provider: IngredientNutritionProvider,
    *,
    tolerant: bool = True,
) -> ImportResult:
    """Execute an import from ``source`` using ``provider`` for recipe nutrition."""
    fetched = source.fetch()  # SourceError propagates: nothing is persisted.

    institution, _ = repo.upsert_institution(session, fetched.institution)
    run = DataImport(
        institution_id=institution.id,
        source_type=source.source_type,
        source_name=source.source_name,
        status=ImportStatus.RUNNING,
        started_at=_now(),
        raw_payload=fetched.raw_payload,
        requested_scope=fetched.requested_scope,
        records_received=len(fetched.menu_items),
    )
    session.add(run)
    session.flush()

    counters = _Counters()
    classification_counts: dict[RecordClassification, int] = defaultdict(int)

    # --- Hierarchy ---------------------------------------------------------
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
                message=f"station {imported_station.slug!r} references unknown venue",
                source_record_ref=imported_station.external_id or imported_station.slug,
            )
            continue
        station, _ = repo.upsert_station(session, parent, imported_station)  # type: ignore[arg-type]
        if imported_station.external_id:
            station_by_key[imported_station.external_id] = station
        station_by_key[imported_station.slug] = station

    # --- Menu items --------------------------------------------------------
    fatal = False
    for result in fetched.menu_items:
        if isinstance(result, MenuItemParseError):
            repo.record_error(
                session,
                run,
                severity=ImportErrorSeverity.ERROR,
                stage=ImportErrorStage.VALIDATE,
                code="malformed_record",
                message=result.message,
                source_record_ref=result.record_ref,
            )
            counters.failed += 1
            counters.skipped += 1
            classification_counts[RecordClassification.INVALID] += 1
            continue

        assert isinstance(result, MenuItemParseOk)
        item = result.item
        classification = classify(item)
        classification_counts[classification] += 1
        record_ref = item.external_id or item.name

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
            continue

        try:
            with session.begin_nested():
                delta = _process_item(
                    session, institution, station_by_key, provider, run, item, classification
                )
        except Exception as exc:  # noqa: BLE001 - converted to a structured error
            repo.record_error(
                session,
                run,
                severity=ImportErrorSeverity.ERROR,
                stage=ImportErrorStage.PERSIST,
                code="persist_failed",
                message=str(exc),
                source_record_ref=record_ref,
            )
            counters.failed += 1
            if not tolerant:
                fatal = True
                break
        else:
            counters.add(delta)

    # --- Finalize ----------------------------------------------------------
    error_count = session.scalar(
        select(func.count())
        .select_from(DataImportError)
        .where(DataImportError.data_import_id == run.id)
    )
    error_count = int(error_count or 0)

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

    if fatal:
        run.status = ImportStatus.FAILED
    elif error_count > 0 or counters.failed > 0:
        run.status = ImportStatus.COMPLETED_WITH_ERRORS
    else:
        run.status = ImportStatus.COMPLETED
    if error_count:
        run.error_summary = f"{error_count} structured error(s)/warning(s); see import_errors"
    session.flush()

    return ImportResult(
        import_id=run.id,
        status=run.status,
        counters=counters,
        classification=dict(classification_counts),
        error_count=error_count,
    )


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
    record_ref = item.external_id or item.name

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
        if r_outcome in ("created", "updated"):
            resolved = [
                resolve_ingredient(parse_ingredient(ing), provider)
                for ing in item.recipe.ingredients
            ]
            for res in resolved:
                if res.provider_food is not None:
                    repo.upsert_provider_food(session, res.provider_food)
            repo.persist_recipe_ingredients(session, version, resolved)

            calc = calculate_recipe_nutrition(item.recipe.servings, resolved)
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
                        ingredient_context=res.parsed.original_text,
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
            elif source_calories is not None and is_large_discrepancy(
                source_calories, calc.per_serving.get("calories")
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
                    detail={
                        "source_calories": str(source_calories),
                        "calculated_calories": str(calc.per_serving.get("calories")),
                    },
                )

    return counters
