"""Relationship traversal tests across the full schema graph."""

from __future__ import annotations

from datetime import date

import factories as f
from sqlalchemy import select
from sqlalchemy.orm import Session

from platewise_db.enums import AllergenDeclarationType, MealPeriod, ReportType
from platewise_db.models import MenuItem, MenuOffering


def test_institution_venue_station_offering_item_chain(db_session: Session) -> None:
    """Institution -> Venue -> Station -> Offering -> Menu Item resolves both ways."""
    institution = f.make_institution(db_session)
    venue = f.make_venue(db_session, institution)
    station = f.make_station(db_session, venue)
    item = f.make_menu_item(db_session, institution)
    offering = f.make_offering(db_session, station, item)

    db_session.expire_all()

    # Downward traversal from the institution.
    loaded = db_session.get(type(institution), institution.id)
    assert [v.id for v in loaded.venues] == [venue.id]
    assert [s.id for s in loaded.venues[0].stations] == [station.id]
    assert [o.id for o in loaded.venues[0].stations[0].offerings] == [offering.id]

    # The offering points at the catalog item (not an embedded copy).
    assert loaded.venues[0].stations[0].offerings[0].menu_item.id == item.id

    # Upward traversal from the offering.
    assert offering.station.venue.institution.id == institution.id


def test_same_item_backs_multiple_offerings(db_session: Session) -> None:
    """One catalog item can back offerings at many stations/dates without duplication."""
    institution = f.make_institution(db_session)
    venue = f.make_venue(db_session, institution)
    grill = f.make_station(db_session, venue, slug="grill", name="Grill")
    hot_line = f.make_station(db_session, venue, slug="hot-line", name="Hot Line")
    item = f.make_menu_item(db_session, institution)

    o1 = f.make_offering(db_session, grill, item, service_date=date(2026, 7, 18))
    o2 = f.make_offering(
        db_session, hot_line, item, service_date=date(2026, 7, 18), meal_period=MealPeriod.DINNER
    )

    assert o1.menu_item_id == o2.menu_item_id == item.id
    offerings = db_session.scalars(
        select(MenuOffering).where(MenuOffering.menu_item_id == item.id)
    ).all()
    assert {o.id for o in offerings} == {o1.id, o2.id}


def test_menu_item_nutrition(db_session: Session) -> None:
    """Menu Item -> Nutrition, including the active-version helper."""
    institution = f.make_institution(db_session)
    item = f.make_menu_item(db_session, institution)
    facts = f.make_nutrition(db_session, item, calories=240)

    db_session.refresh(item)
    assert [n.id for n in item.nutrition_facts] == [facts.id]
    assert [n.id for n in item.active_nutrition] == [facts.id]
    display = item.display_nutrition()
    assert display is not None
    assert display.calories == 240
    assert facts.menu_item.id == item.id


def test_menu_item_ingredients(db_session: Session) -> None:
    """Menu Item -> Ingredients via association object and proxy."""
    institution = f.make_institution(db_session)
    item = f.make_menu_item(db_session, institution)
    chicken = f.make_ingredient(db_session, institution, name="Chicken Breast")
    oil = f.make_ingredient(db_session, institution, name="Olive Oil")
    f.link_ingredient(db_session, item, chicken, sort_order=0)
    f.link_ingredient(db_session, item, oil, sort_order=1, quantity=2, unit="tbsp")

    db_session.refresh(item)
    assert {link.ingredient.name for link in item.ingredient_links} == {
        "Chicken Breast",
        "Olive Oil",
    }
    # Association proxy exposes ingredients directly.
    assert {ing.name for ing in item.ingredients} == {"Chicken Breast", "Olive Oil"}
    # Reverse side.
    assert chicken.menu_item_links[0].menu_item.id == item.id


def test_menu_item_allergens(db_session: Session) -> None:
    """Menu Item -> Allergens with a declaration type."""
    institution = f.make_institution(db_session)
    item = f.make_menu_item(db_session, institution)
    peanut = f.make_allergen(db_session, name="Peanut")
    f.link_allergen(db_session, item, peanut, declaration_type=AllergenDeclarationType.MAY_CONTAIN)

    db_session.refresh(item)
    assert [link.allergen.name for link in item.allergen_links] == ["Peanut"]
    assert item.allergen_links[0].declaration_type == AllergenDeclarationType.MAY_CONTAIN
    assert [a.name for a in item.allergens] == ["Peanut"]


def test_menu_item_dietary_tags(db_session: Session) -> None:
    """Menu Item -> Dietary Tags with confidence."""
    institution = f.make_institution(db_session)
    item = f.make_menu_item(db_session, institution)
    tag = f.make_dietary_tag(db_session, name="Gluten Free")
    f.link_dietary_tag(db_session, item, tag, confidence=0.9)

    db_session.refresh(item)
    assert [t.name for t in item.dietary_tags] == ["Gluten Free"]
    assert float(item.dietary_tag_links[0].confidence) == 0.9


def test_offering_reports(db_session: Session) -> None:
    """Offering -> Reports, including a replacement pointing at a catalog item."""
    institution = f.make_institution(db_session)
    venue = f.make_venue(db_session, institution)
    station = f.make_station(db_session, venue)
    turkey = f.make_menu_item(db_session, institution, name="Turkey Burger")
    chicken = f.make_menu_item(db_session, institution, name="Grilled Chicken Breast")
    offering = f.make_offering(db_session, station, turkey)

    report = f.make_report(db_session, offering, report_type=ReportType.SOLD_OUT)
    replacement = f.make_report(
        db_session,
        offering,
        reporter_id="device-2",
        report_type=ReportType.REPLACEMENT,
        replacement_menu_item_id=chicken.id,
    )

    db_session.refresh(offering)
    assert {r.id for r in offering.reports} == {report.id, replacement.id}
    assert replacement.replacement_menu_item.id == chicken.id
    assert report.offering.id == offering.id


def test_import_tracks_created_records(db_session: Session) -> None:
    """Import -> Created records (menu items and offerings) is traceable."""
    institution = f.make_institution(db_session)
    venue = f.make_venue(db_session, institution)
    station = f.make_station(db_session, venue)
    data_import = f.make_import(db_session, institution)

    item = f.make_menu_item(db_session, institution, created_by_import_id=data_import.id)
    offering = f.make_offering(db_session, station, item, created_by_import_id=data_import.id)

    db_session.refresh(data_import)
    assert [mi.id for mi in data_import.created_menu_items] == [item.id]
    assert [o.id for o in data_import.created_offerings] == [offering.id]
    assert item.created_by_import.id == data_import.id
    assert data_import.institution.id == institution.id


def test_menu_item_persists_when_absent_from_menus(db_session: Session) -> None:
    """A catalog item survives deletion of the offering that referenced it."""
    institution = f.make_institution(db_session)
    venue = f.make_venue(db_session, institution)
    station = f.make_station(db_session, venue)
    item = f.make_menu_item(db_session, institution)
    offering = f.make_offering(db_session, station, item)

    db_session.delete(offering)
    db_session.flush()

    assert db_session.get(MenuItem, item.id) is not None
