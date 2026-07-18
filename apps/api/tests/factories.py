"""Lightweight builders for constructing schema-validation fixture data.

These are intentionally minimal -- just enough to exercise relationships and
constraints. They are *not* the real importer (that is a later milestone).
Each helper adds the object to the session and flushes so database defaults
(ids, timestamps) are populated.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.db.enums import (
    ImportSourceType,
    ImportStatus,
    InstitutionType,
    MealPeriod,
    ReportType,
    VenueType,
)
from app.db.models import (
    Allergen,
    DataImport,
    DietaryTag,
    Ingredient,
    Institution,
    MenuItem,
    MenuItemAllergen,
    MenuItemDietaryTag,
    MenuItemIngredient,
    MenuOffering,
    NutritionFacts,
    OfferingReport,
    Station,
    Venue,
)


def _normalize(value: str) -> str:
    return " ".join(value.strip().lower().split())


def make_institution(session: Session, *, slug: str = "uga", **kwargs: Any) -> Institution:
    institution = Institution(
        name=kwargs.pop("name", "University of Georgia"),
        slug=slug,
        institution_type=kwargs.pop("institution_type", InstitutionType.UNIVERSITY),
        timezone=kwargs.pop("timezone", "America/New_York"),
        **kwargs,
    )
    session.add(institution)
    session.flush()
    return institution


def make_venue(
    session: Session, institution: Institution, *, slug: str = "bolton", **kwargs: Any
) -> Venue:
    venue = Venue(
        institution_id=institution.id,
        name=kwargs.pop("name", "Bolton Dining Commons"),
        slug=slug,
        venue_type=kwargs.pop("venue_type", VenueType.DINING_HALL),
        **kwargs,
    )
    session.add(venue)
    session.flush()
    return venue


def make_station(session: Session, venue: Venue, *, slug: str = "grill", **kwargs: Any) -> Station:
    station = Station(
        venue_id=venue.id,
        name=kwargs.pop("name", "Grill"),
        slug=slug,
        **kwargs,
    )
    session.add(station)
    session.flush()
    return station


def make_menu_item(
    session: Session,
    institution: Institution,
    *,
    name: str = "Grilled Chicken Breast",
    **kwargs: Any,
) -> MenuItem:
    item = MenuItem(
        institution_id=institution.id,
        name=name,
        normalized_name=kwargs.pop("normalized_name", _normalize(name)),
        **kwargs,
    )
    session.add(item)
    session.flush()
    return item


def make_nutrition(session: Session, menu_item: MenuItem, **kwargs: Any) -> NutritionFacts:
    facts = NutritionFacts(
        menu_item_id=menu_item.id,
        serving_size=kwargs.pop("serving_size", 1),
        serving_unit=kwargs.pop("serving_unit", "breast"),
        calories=kwargs.pop("calories", 240),
        protein_g=kwargs.pop("protein_g", 36),
        carbohydrates_g=kwargs.pop("carbohydrates_g", 2),
        fat_g=kwargs.pop("fat_g", 8),
        **kwargs,
    )
    session.add(facts)
    session.flush()
    return facts


def make_ingredient(
    session: Session, institution: Institution, *, name: str = "Chicken Breast", **kwargs: Any
) -> Ingredient:
    ingredient = Ingredient(
        institution_id=institution.id,
        name=name,
        normalized_name=kwargs.pop("normalized_name", _normalize(name)),
        **kwargs,
    )
    session.add(ingredient)
    session.flush()
    return ingredient


def link_ingredient(
    session: Session, menu_item: MenuItem, ingredient: Ingredient, **kwargs: Any
) -> MenuItemIngredient:
    link = MenuItemIngredient(
        menu_item_id=menu_item.id, ingredient_id=ingredient.id, **kwargs
    )
    session.add(link)
    session.flush()
    return link


def make_allergen(session: Session, *, name: str = "Peanut", **kwargs: Any) -> Allergen:
    allergen = Allergen(name=name, normalized_name=kwargs.pop("normalized_name", _normalize(name)))
    session.add(allergen)
    session.flush()
    return allergen


def link_allergen(
    session: Session, menu_item: MenuItem, allergen: Allergen, **kwargs: Any
) -> MenuItemAllergen:
    link = MenuItemAllergen(menu_item_id=menu_item.id, allergen_id=allergen.id, **kwargs)
    session.add(link)
    session.flush()
    return link


def make_dietary_tag(session: Session, *, name: str = "Gluten Free", **kwargs: Any) -> DietaryTag:
    tag = DietaryTag(name=name, normalized_name=kwargs.pop("normalized_name", _normalize(name)))
    session.add(tag)
    session.flush()
    return tag


def link_dietary_tag(
    session: Session, menu_item: MenuItem, tag: DietaryTag, **kwargs: Any
) -> MenuItemDietaryTag:
    link = MenuItemDietaryTag(menu_item_id=menu_item.id, dietary_tag_id=tag.id, **kwargs)
    session.add(link)
    session.flush()
    return link


def make_offering(
    session: Session,
    station: Station,
    menu_item: MenuItem,
    *,
    service_date: date | None = None,
    meal_period: MealPeriod = MealPeriod.LUNCH,
    **kwargs: Any,
) -> MenuOffering:
    offering = MenuOffering(
        station_id=station.id,
        menu_item_id=menu_item.id,
        service_date=service_date or date(2026, 7, 18),
        meal_period=meal_period,
        **kwargs,
    )
    session.add(offering)
    session.flush()
    return offering


def make_report(
    session: Session,
    offering: MenuOffering,
    *,
    reporter_id: str = "device-1",
    report_type: ReportType = ReportType.SOLD_OUT,
    **kwargs: Any,
) -> OfferingReport:
    report = OfferingReport(
        offering_id=offering.id,
        reporter_id=reporter_id,
        report_type=report_type,
        **kwargs,
    )
    session.add(report)
    session.flush()
    return report


def make_import(
    session: Session,
    institution: Institution,
    *,
    source_type: ImportSourceType = ImportSourceType.FIXTURE,
    **kwargs: Any,
) -> DataImport:
    data_import = DataImport(
        institution_id=institution.id,
        source_type=source_type,
        status=kwargs.pop("status", ImportStatus.COMPLETED),
        started_at=kwargs.pop("started_at", datetime.now(UTC)),
        **kwargs,
    )
    session.add(data_import)
    session.flush()
    return data_import
