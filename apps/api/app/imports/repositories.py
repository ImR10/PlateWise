"""Idempotent persistence for imported records.

Every write is an upsert keyed on deterministic identity:

* Hierarchy/catalog rows: ``(parent, source_system, external_id)`` when an
  external id exists (the source-neutral identity); otherwise a scoped fallback
  key (slug / offering slot). Names are never used as an authoritative key.
* Source-provided nutrition: one active row per ``(menu_item, source_provided)``,
  versioned by ``content_hash``.
* Recipe versions: one active version per menu item, versioned by
  ``content_hash``; a content change supersedes the prior version (history
  preserved) instead of mutating it.
* Recipe-calculated nutrition: one active row per
  ``(menu_item, recipe_calculated)`` tied to the active recipe version.

Re-importing identical source data changes nothing (all hashes match).
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.enums import (
    ImportErrorSeverity,
    ImportErrorStage,
    NutritionProvenance,
    NutritionReviewStatus,
    NutritionSourceType,
)
from app.db.models import (
    DataImport,
    DataImportError,
    Institution,
    MenuItem,
    MenuOffering,
    NutritionFacts,
    ProviderFood,
    ProviderFoodPortion,
    RecipeIngredient,
    RecipeVersion,
    Station,
    Venue,
)
from app.imports.contracts import (
    ImportedInstitution,
    ImportedMenuItem,
    ImportedRecipe,
    ImportedStation,
    ImportedVenue,
)
from app.imports.decimal_utils import quantize_grams, quantize_quantity, quantize_serving
from app.imports.enums import NUTRIENT_FIELDS
from app.imports.normalizers import content_hash, normalize_name
from app.imports.nutrition.normalizer import NormalizedNutrition
from app.imports.nutrition.provider import ProviderFoodData
from app.imports.recipes.calculator import CalculatedNutrition
from app.imports.recipes.resolver import ResolvedIngredient

Outcome = Literal["created", "updated", "unchanged"]


def _now() -> datetime:
    return datetime.now(UTC)


# --- Hierarchy & catalog --------------------------------------------------


def upsert_institution(
    session: Session, imported: ImportedInstitution
) -> tuple[Institution, Outcome]:
    digest = content_hash(
        [imported.name, imported.slug, imported.institution_type.value, imported.timezone]
    )
    existing: Institution | None = None
    if imported.external_id:
        existing = session.scalar(
            select(Institution).where(
                Institution.source_system == imported.source_system,
                Institution.external_id == imported.external_id,
            )
        )
    if existing is None:
        existing = session.scalar(select(Institution).where(Institution.slug == imported.slug))

    if existing is None:
        institution = Institution(
            source_system=imported.source_system,
            external_id=imported.external_id,
            name=imported.name,
            slug=imported.slug,
            institution_type=imported.institution_type,
            timezone=imported.timezone,
            content_hash=digest,
        )
        session.add(institution)
        session.flush()
        return institution, "created"

    if existing.content_hash == digest:
        return existing, "unchanged"
    existing.name = imported.name
    existing.institution_type = imported.institution_type
    existing.timezone = imported.timezone
    existing.content_hash = digest
    session.flush()
    return existing, "updated"


def upsert_venue(
    session: Session, institution: Institution, imported: ImportedVenue
) -> tuple[Venue, Outcome]:
    digest = content_hash([imported.name, imported.slug, imported.venue_type.value])
    existing: Venue | None = None
    if imported.external_id:
        existing = session.scalar(
            select(Venue).where(
                Venue.institution_id == institution.id,
                Venue.source_system == imported.source_system,
                Venue.external_id == imported.external_id,
            )
        )
    if existing is None:
        existing = session.scalar(
            select(Venue).where(
                Venue.institution_id == institution.id, Venue.slug == imported.slug
            )
        )
    if existing is None:
        venue = Venue(
            institution_id=institution.id,
            source_system=imported.source_system,
            external_id=imported.external_id,
            name=imported.name,
            slug=imported.slug,
            venue_type=imported.venue_type,
            content_hash=digest,
        )
        session.add(venue)
        session.flush()
        return venue, "created"
    if existing.content_hash == digest:
        return existing, "unchanged"
    existing.name = imported.name
    existing.venue_type = imported.venue_type
    existing.content_hash = digest
    session.flush()
    return existing, "updated"


def upsert_station(
    session: Session, venue: Venue, imported: ImportedStation
) -> tuple[Station, Outcome]:
    digest = content_hash([imported.name, imported.slug, imported.station_type])
    existing: Station | None = None
    if imported.external_id:
        existing = session.scalar(
            select(Station).where(
                Station.venue_id == venue.id,
                Station.source_system == imported.source_system,
                Station.external_id == imported.external_id,
            )
        )
    if existing is None:
        existing = session.scalar(
            select(Station).where(Station.venue_id == venue.id, Station.slug == imported.slug)
        )
    if existing is None:
        station = Station(
            venue_id=venue.id,
            source_system=imported.source_system,
            external_id=imported.external_id,
            name=imported.name,
            slug=imported.slug,
            station_type=imported.station_type,
            content_hash=digest,
        )
        session.add(station)
        session.flush()
        return station, "created"
    if existing.content_hash == digest:
        return existing, "unchanged"
    existing.name = imported.name
    existing.station_type = imported.station_type
    existing.content_hash = digest
    session.flush()
    return existing, "updated"


def upsert_menu_item(
    session: Session,
    institution: Institution,
    imported: ImportedMenuItem,
    import_run: DataImport,
) -> tuple[MenuItem, Outcome]:
    serving_size = (
        None if imported.serving_size is None else quantize_serving(imported.serving_size)
    )
    normalized = normalize_name(imported.name)
    digest = content_hash(
        [imported.name, normalized, imported.description, serving_size, imported.serving_unit]
    )
    existing: MenuItem | None = None
    if imported.external_id:
        existing = session.scalar(
            select(MenuItem).where(
                MenuItem.institution_id == institution.id,
                MenuItem.source_system == imported.source_system,
                MenuItem.external_id == imported.external_id,
            )
        )
    # Deliberately no name-based fallback: two distinct items may share a name.

    if existing is None:
        item = MenuItem(
            institution_id=institution.id,
            source_system=imported.source_system,
            external_id=imported.external_id,
            name=imported.name,
            normalized_name=normalized,
            description=imported.description,
            default_serving_size=serving_size,
            default_serving_unit=imported.serving_unit,
            content_hash=digest,
            created_by_import_id=import_run.id,
            updated_by_import_id=import_run.id,
        )
        session.add(item)
        session.flush()
        return item, "created"

    if existing.content_hash == digest:
        return existing, "unchanged"
    existing.name = imported.name
    existing.normalized_name = normalized
    existing.description = imported.description
    existing.default_serving_size = serving_size
    existing.default_serving_unit = imported.serving_unit
    existing.content_hash = digest
    existing.updated_by_import_id = import_run.id
    session.flush()
    return existing, "updated"


def upsert_offering(
    session: Session,
    station: Station,
    menu_item: MenuItem,
    imported: ImportedMenuItem,
    import_run: DataImport,
) -> tuple[MenuOffering, Outcome]:
    assert imported.service_date is not None and imported.meal_period is not None
    existing: MenuOffering | None = None
    if imported.external_id:
        existing = session.scalar(
            select(MenuOffering).where(
                MenuOffering.station_id == station.id,
                MenuOffering.source_system == imported.source_system,
                MenuOffering.external_id == imported.external_id,
            )
        )
    if existing is None:
        existing = session.scalar(
            select(MenuOffering).where(
                MenuOffering.station_id == station.id,
                MenuOffering.menu_item_id == menu_item.id,
                MenuOffering.service_date == imported.service_date,
                MenuOffering.meal_period == imported.meal_period,
                MenuOffering.starts_at.is_(None),
            )
        )
    if existing is None:
        offering = MenuOffering(
            station_id=station.id,
            menu_item_id=menu_item.id,
            source_system=imported.source_system,
            external_id=imported.external_id,
            service_date=imported.service_date,
            meal_period=imported.meal_period,
            created_by_import_id=import_run.id,
            updated_by_import_id=import_run.id,
        )
        session.add(offering)
        session.flush()
        return offering, "created"
    return existing, "unchanged"


def upsert_provider_food(session: Session, food: ProviderFoodData) -> ProviderFood:
    existing = session.scalar(
        select(ProviderFood).where(
            ProviderFood.provider == food.provider,
            ProviderFood.provider_food_id == food.provider_food_id,
        )
    )
    if existing is not None:
        return existing
    row = ProviderFood(
        provider=food.provider,
        provider_food_id=food.provider_food_id,
        name=food.name,
        reference_grams=food.reference_grams,
        raw_metadata=food.raw_metadata,
        **{field: getattr(food.nutrients, field) for field in NUTRIENT_FIELDS},
    )
    session.add(row)
    session.flush()
    for portion in food.portions:
        session.add(
            ProviderFoodPortion(
                provider_food_id=row.id,
                portion_description=portion.description,
                gram_weight=portion.gram_weight,
            )
        )
    session.flush()
    return row


# --- Nutrition (source-provided) ------------------------------------------


def upsert_source_nutrition(
    session: Session,
    menu_item: MenuItem,
    normalized: NormalizedNutrition,
    import_run: DataImport,
) -> tuple[NutritionFacts, Outcome]:
    active = session.scalar(
        select(NutritionFacts).where(
            NutritionFacts.menu_item_id == menu_item.id,
            NutritionFacts.provenance == NutritionProvenance.SOURCE_PROVIDED,
            NutritionFacts.valid_until.is_(None),
        )
    )
    if active is not None and active.content_hash == normalized.content_hash:
        return active, "unchanged"

    now = _now()
    if active is not None:
        active.valid_until = now
        session.flush()  # free the (menu_item, provenance) active slot first

    facts = NutritionFacts(
        menu_item_id=menu_item.id,
        provenance=NutritionProvenance.SOURCE_PROVIDED,
        source_type=NutritionSourceType.OFFICIAL,
        source_reference=normalized.source_reference,
        serving_size=normalized.serving_size,
        serving_unit=normalized.serving_unit,
        is_complete=True,
        review_status=NutritionReviewStatus.NOT_REQUIRED,
        content_hash=normalized.content_hash,
        created_by_import_id=import_run.id,
        updated_by_import_id=import_run.id,
        **{field: normalized.nutrients[field] for field in NUTRIENT_FIELDS},
    )
    session.add(facts)
    session.flush()
    return facts, ("updated" if active is not None else "created")


# --- Recipes --------------------------------------------------------------


def recipe_content_hash(recipe: ImportedRecipe) -> str:
    parts: list[object] = [
        recipe.source_system,
        recipe.external_id,
        recipe.yield_quantity,
        recipe.yield_unit,
        recipe.servings,
        recipe.source_text,
    ]
    for ing in recipe.ingredients:
        parts.extend(
            [
                ing.line_no,
                ing.original_text,
                ing.quantity,
                ing.unit,
                ing.name,
                ing.preparation,
                ing.is_optional,
                ing.external_food_id,
            ]
        )
    return content_hash(parts)


def upsert_recipe_version(
    session: Session,
    menu_item: MenuItem,
    recipe: ImportedRecipe,
    import_run: DataImport,
) -> tuple[RecipeVersion, Outcome]:
    digest = recipe_content_hash(recipe)
    active = session.scalar(
        select(RecipeVersion).where(
            RecipeVersion.menu_item_id == menu_item.id,
            RecipeVersion.valid_until.is_(None),
        )
    )
    if active is not None and active.content_hash == digest:
        return active, "unchanged"

    now = _now()
    version_no = 1
    if active is not None:
        active.valid_until = now
        version_no = active.version_no + 1
        session.flush()

    version = RecipeVersion(
        menu_item_id=menu_item.id,
        source_system=recipe.source_system,
        external_id=recipe.external_id,
        version_no=version_no,
        yield_quantity=(
            None if recipe.yield_quantity is None else quantize_quantity(recipe.yield_quantity)
        ),
        yield_unit=recipe.yield_unit,
        servings=None if recipe.servings is None else quantize_quantity(recipe.servings),
        source_text=recipe.source_text,
        content_hash=digest,
        created_by_import_id=import_run.id,
    )
    session.add(version)
    session.flush()
    return version, ("updated" if active is not None else "created")


def persist_recipe_ingredients(
    session: Session,
    version: RecipeVersion,
    resolved: list[ResolvedIngredient],
    provider_food_ids: dict[tuple[str, str], object],
) -> None:
    """Persist ingredient rows for a freshly-created recipe version."""
    for item in resolved:
        parsed = item.parsed
        provider_food_id = None
        if item.provider_food is not None:
            provider_food_id = provider_food_ids.get(
                (item.provider_food.provider, item.provider_food.provider_food_id)
            )
        session.add(
            RecipeIngredient(
                recipe_version_id=version.id,
                line_no=parsed.line_no,
                original_text=parsed.original_text,
                parsed_quantity=(
                    None if parsed.quantity is None else quantize_quantity(parsed.quantity)
                ),
                parsed_unit=parsed.unit,
                normalized_ingredient_name=parsed.normalized_name,
                preparation_notes=parsed.preparation,
                is_optional=parsed.is_optional,
                raw_or_cooked=parsed.raw_or_cooked,
                grams=None if item.grams is None else quantize_grams(item.grams),
                provider_food_id=provider_food_id,
                match_method=item.match_method,
                resolution_status=item.status,
                confidence=item.confidence,
                error_detail=item.error_detail,
            )
        )
    session.flush()
def upsert_calculated_nutrition(
    session: Session,
    menu_item: MenuItem,
    version: RecipeVersion,
    calc: CalculatedNutrition,
    import_run: DataImport,
) -> tuple[NutritionFacts, Outcome]:
    active = session.scalar(
        select(NutritionFacts).where(
            NutritionFacts.menu_item_id == menu_item.id,
            NutritionFacts.provenance == NutritionProvenance.RECIPE_CALCULATED,
            NutritionFacts.valid_until.is_(None),
        )
    )
    # Idempotent: calculated nutrition tied to the same active recipe version.
    if active is not None and active.recipe_version_id == version.id:
        return active, "unchanged"

    now = _now()
    if active is not None:
        active.valid_until = now
        session.flush()

    review = (
        NutritionReviewStatus.NOT_REQUIRED
        if calc.is_complete
        else NutritionReviewStatus.NEEDS_REVIEW
    )
    facts = NutritionFacts(
        menu_item_id=menu_item.id,
        provenance=NutritionProvenance.RECIPE_CALCULATED,
        source_type=NutritionSourceType.RECIPE_CALCULATED,
        serving_size=Decimal("1"),
        serving_unit="serving",
        is_complete=calc.is_complete,
        is_estimated=not calc.is_complete,
        review_status=review,
        calculation_status=calc.status,
        calculation_version=calc.calculation_version,
        calculated_at=now,
        recipe_version_id=version.id,
        created_by_import_id=import_run.id,
        updated_by_import_id=import_run.id,
        **{field: calc.per_serving.get(field) for field in NUTRIENT_FIELDS},
    )
    session.add(facts)
    session.flush()
    return facts, ("updated" if active is not None else "created")


def get_active_calculated_nutrition(
    session: Session, menu_item: MenuItem
) -> NutritionFacts | None:
    """Return the active recipe-calculated nutrition row for ``menu_item``."""
    return session.scalar(
        select(NutritionFacts).where(
            NutritionFacts.menu_item_id == menu_item.id,
            NutritionFacts.provenance == NutritionProvenance.RECIPE_CALCULATED,
            NutritionFacts.valid_until.is_(None),
        )
    )


# --- Errors ---------------------------------------------------------------


def record_error(
    session: Session,
    import_run: DataImport,
    *,
    severity: ImportErrorSeverity,
    stage: ImportErrorStage,
    code: str,
    message: str,
    source_record_ref: str | None = None,
    menu_item_id=None,
    ingredient_context: str | None = None,
    detail: dict | None = None,
) -> DataImportError:
    error = DataImportError(
        data_import_id=import_run.id,
        severity=severity,
        stage=stage,
        code=code,
        message=message,
        source_record_ref=source_record_ref,
        menu_item_id=menu_item_id,
        ingredient_context=ingredient_context,
        detail=detail,
    )
    session.add(error)
    session.flush()
    return error
