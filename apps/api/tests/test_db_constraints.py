"""Constraint tests: uniqueness, foreign keys, cascades, nullability, enums."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta

import factories as f
import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import DataError, IntegrityError
from sqlalchemy.orm import Session

from app.db.enums import MealPeriod, ModerationStatus, ReportType
from app.db.models import (
    Institution,
    MenuItem,
    MenuOffering,
    NutritionFacts,
    OfferingReport,
    Station,
    Venue,
)

# --- Uniqueness -----------------------------------------------------------


def test_institution_slug_unique(db_session: Session) -> None:
    f.make_institution(db_session, slug="dupe")
    db_session.add(Institution(name="Other", slug="dupe"))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_venue_slug_unique_per_institution(db_session: Session) -> None:
    institution = f.make_institution(db_session)
    f.make_venue(db_session, institution, slug="bolton")
    # Same slug under a *different* institution is allowed.
    other = f.make_institution(db_session, slug="gatech", name="Georgia Tech")
    f.make_venue(db_session, other, slug="bolton")
    # Duplicate slug within the same institution is rejected.
    db_session.add(Venue(institution_id=institution.id, name="Bolton 2", slug="bolton"))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_menu_item_external_id_unique_but_nulls_allowed(db_session: Session) -> None:
    institution = f.make_institution(db_session)
    # Two items with NULL external_id coexist (partial unique index).
    f.make_menu_item(db_session, institution, name="Item A", external_id=None)
    f.make_menu_item(db_session, institution, name="Item B", external_id=None)
    # A concrete external_id must be unique within the institution.
    f.make_menu_item(db_session, institution, name="Item C", external_id="EXT-1")
    db_session.add(
        MenuItem(
            institution_id=institution.id,
            name="Item D",
            normalized_name="item d",
            external_id="EXT-1",
        )
    )
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_offering_slot_unique_including_null_starts_at(db_session: Session) -> None:
    """UNIQUE(... starts_at) with NULLS NOT DISTINCT dedupes NULL start times."""
    institution = f.make_institution(db_session)
    venue = f.make_venue(db_session, institution)
    station = f.make_station(db_session, venue)
    item = f.make_menu_item(db_session, institution)
    f.make_offering(db_session, station, item, starts_at=None)
    db_session.add(
        MenuOffering(
            station_id=station.id,
            menu_item_id=item.id,
            service_date=date(2026, 7, 18),
            meal_period=MealPeriod.LUNCH,
            starts_at=None,
        )
    )
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_one_active_nutrition_record_per_item(db_session: Session) -> None:
    institution = f.make_institution(db_session)
    item = f.make_menu_item(db_session, institution)
    # An archived (valid_until set) version plus an active version is fine.
    f.make_nutrition(
        db_session,
        item,
        valid_from=datetime(2026, 1, 1, tzinfo=UTC),
        valid_until=datetime(2026, 6, 1, tzinfo=UTC),
    )
    f.make_nutrition(db_session, item)  # active (valid_until is NULL)
    # A second active record violates the partial unique index.
    db_session.add(NutritionFacts(menu_item_id=item.id))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_one_active_report_per_reporter_and_category(db_session: Session) -> None:
    institution = f.make_institution(db_session)
    venue = f.make_venue(db_session, institution)
    station = f.make_station(db_session, venue)
    item = f.make_menu_item(db_session, institution)
    offering = f.make_offering(db_session, station, item)

    f.make_report(db_session, offering, reporter_id="dev-1", report_type=ReportType.SOLD_OUT)
    # Same reporter + same offering + same category, still active -> rejected.
    db_session.add(
        OfferingReport(
            offering_id=offering.id, reporter_id="dev-1", report_type=ReportType.SOLD_OUT
        )
    )
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_retracted_report_frees_the_active_slot(db_session: Session) -> None:
    institution = f.make_institution(db_session)
    venue = f.make_venue(db_session, institution)
    station = f.make_station(db_session, venue)
    item = f.make_menu_item(db_session, institution)
    offering = f.make_offering(db_session, station, item)

    first = f.make_report(
        db_session, offering, reporter_id="dev-1", report_type=ReportType.SOLD_OUT
    )
    first.moderation_status = ModerationStatus.RETRACTED
    first.retracted_at = datetime.now(UTC)
    db_session.flush()

    # A new active report of the same category is now allowed.
    second = f.make_report(
        db_session, offering, reporter_id="dev-1", report_type=ReportType.SOLD_OUT
    )
    db_session.flush()
    assert second.id is not None


# --- Foreign keys ---------------------------------------------------------


def test_foreign_key_violation_rejected(db_session: Session) -> None:
    """A venue referencing a non-existent institution is rejected."""
    db_session.add(
        Venue(institution_id=uuid.uuid4(), name="Ghost", slug="ghost")
    )
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_offering_restricts_menu_item_deletion(db_session: Session) -> None:
    """ondelete=RESTRICT protects a catalog item still referenced by an offering."""
    institution = f.make_institution(db_session)
    venue = f.make_venue(db_session, institution)
    station = f.make_station(db_session, venue)
    item = f.make_menu_item(db_session, institution)
    f.make_offering(db_session, station, item)

    db_session.delete(item)
    with pytest.raises(IntegrityError):
        db_session.flush()


# --- Cascade behavior -----------------------------------------------------


def test_deleting_institution_cascades(db_session: Session) -> None:
    institution = f.make_institution(db_session)
    venue = f.make_venue(db_session, institution)
    station = f.make_station(db_session, venue)
    item = f.make_menu_item(db_session, institution)
    f.make_offering(db_session, station, item)

    db_session.delete(institution)
    db_session.flush()
    db_session.expire_all()

    assert db_session.scalar(select(func.count()).select_from(Venue)) == 0
    assert db_session.scalar(select(func.count()).select_from(Station)) == 0
    assert db_session.scalar(select(func.count()).select_from(MenuItem)) == 0
    assert db_session.scalar(select(func.count()).select_from(MenuOffering)) == 0


def test_deleting_offering_cascades_reports(db_session: Session) -> None:
    institution = f.make_institution(db_session)
    venue = f.make_venue(db_session, institution)
    station = f.make_station(db_session, venue)
    item = f.make_menu_item(db_session, institution)
    offering = f.make_offering(db_session, station, item)
    f.make_report(db_session, offering)

    db_session.delete(offering)
    db_session.flush()
    db_session.expire_all()

    assert db_session.scalar(select(func.count()).select_from(OfferingReport)) == 0


def test_replacement_menu_item_set_null_on_delete(db_session: Session) -> None:
    """Deleting the replacement catalog item nulls the report pointer (SET NULL)."""
    institution = f.make_institution(db_session)
    venue = f.make_venue(db_session, institution)
    station = f.make_station(db_session, venue)
    served = f.make_menu_item(db_session, institution, name="Turkey Burger")
    replacement = f.make_menu_item(db_session, institution, name="Grilled Chicken")
    offering = f.make_offering(db_session, station, served)
    report = f.make_report(
        db_session,
        offering,
        report_type=ReportType.REPLACEMENT,
        replacement_menu_item_id=replacement.id,
    )

    db_session.delete(replacement)
    db_session.flush()
    db_session.refresh(report)
    assert report.replacement_menu_item_id is None


# --- Nullability ----------------------------------------------------------


def test_required_columns_reject_null(db_session: Session) -> None:
    db_session.add(Institution(name=None, slug="no-name"))  # type: ignore[arg-type]
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_optional_columns_accept_null(db_session: Session) -> None:
    institution = f.make_institution(db_session)
    venue = f.make_venue(db_session, institution)
    station = f.make_station(db_session, venue)
    # No external_id / description / nutrition -> all nullable.
    item = f.make_menu_item(db_session, institution, external_id=None, description=None)
    offering = f.make_offering(
        db_session, station, item, starts_at=None, ends_at=None, source_type=None
    )
    db_session.flush()
    assert item.external_id is None
    assert offering.starts_at is None


# --- Enum validation ------------------------------------------------------


def test_invalid_enum_value_rejected(db_session: Session) -> None:
    """The database rejects a value outside the meal_period enum."""
    institution = f.make_institution(db_session)
    venue = f.make_venue(db_session, institution)
    station = f.make_station(db_session, venue)
    item = f.make_menu_item(db_session, institution)
    with pytest.raises((DataError, IntegrityError)):
        db_session.execute(
            text(
                "INSERT INTO menu_offerings (station_id, menu_item_id, service_date, meal_period) "
                "VALUES (:station_id, :menu_item_id, :service_date, 'midnight_snack')"
            ),
            {
                "station_id": station.id,
                "menu_item_id": item.id,
                "service_date": date(2026, 7, 18),
            },
        )


def test_confidence_check_constraint(db_session: Session) -> None:
    """Dietary-tag confidence must be within [0, 1]."""
    institution = f.make_institution(db_session)
    item = f.make_menu_item(db_session, institution)
    tag = f.make_dietary_tag(db_session, name="Vegan")
    with pytest.raises(IntegrityError):
        f.link_dietary_tag(db_session, item, tag, confidence=1.5)


# --- Timestamps -----------------------------------------------------------


def test_timestamps_autopopulate_and_update(db_session: Session) -> None:
    institution = f.make_institution(db_session)
    assert institution.created_at is not None
    assert institution.updated_at is not None
    original = institution.updated_at

    institution.name = "Renamed University"
    db_session.flush()
    db_session.refresh(institution)
    assert institution.updated_at >= original


def test_reported_at_defaults_to_server_time(db_session: Session) -> None:
    institution = f.make_institution(db_session)
    venue = f.make_venue(db_session, institution)
    station = f.make_station(db_session, venue)
    item = f.make_menu_item(db_session, institution)
    offering = f.make_offering(db_session, station, item)
    report = f.make_report(db_session, offering)
    db_session.refresh(report)
    assert report.reported_at is not None
    assert report.reported_at <= datetime.now(UTC) + timedelta(minutes=5)
