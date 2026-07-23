"""Idempotent development seeding through the real import pipeline.

Runs ``platewise_api.imports.run_import`` with the deterministic fixture
payload from :mod:`platewise_api.dev.seed_data`, so every seeded row goes
through the same validation, normalization, provenance, and counter logic as a
real import. Re-running against the same database and service date is a no-op
(the pipeline upserts on stable external ids).

The one deliberate exception: after a fully successful import, allergen and
dietary-tag links are applied directly through the ORM because the import
pipeline does not persist that metadata yet. The supplement records imported
provenance, is idempotent (get-or-create by normalized name, link-if-absent),
and should be deleted once allergen/tag import wiring lands.

Usage (inside Compose):

    docker compose exec api uv run python -m platewise_api.dev.seed

or on the host with a local database URL:

    DATABASE_URL=postgresql+psycopg://platewise:platewise_dev_password@localhost:5432/platewise \
        api/.venv/bin/python -m platewise_api.dev.seed
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date

from platewise_db.enums import ImportStatus, ProvenanceSourceType
from platewise_db.models import Allergen, DietaryTag, MenuItem, MenuItemAllergen, MenuItemDietaryTag
from platewise_db.normalizers import normalize_name
from sqlalchemy import select
from sqlalchemy.orm import Session

from platewise_api.dev.seed_data import (
    ALLERGEN_ASSIGNMENTS,
    DIETARY_TAG_ASSIGNMENTS,
    SOURCE_NAME,
    SOURCE_SYSTEM,
    build_payload,
    build_provider,
)
from platewise_api.imports import FixtureDiningSource, ImportResult, run_import


@dataclass(frozen=True)
class SeedSummary:
    """Outcome of one seed run."""

    import_result: ImportResult
    allergen_links_created: int
    dietary_tag_links_created: int


def _seed_menu_item(session: Session, external_id: str) -> MenuItem | None:
    return session.scalar(
        select(MenuItem).where(
            MenuItem.source_system == SOURCE_SYSTEM,
            MenuItem.external_id == external_id,
        )
    )


def _get_or_create(session: Session, model: type[Allergen | DietaryTag], name: str):
    normalized = normalize_name(name)
    record = session.scalar(select(model).where(model.normalized_name == normalized))
    if record is None:
        record = model(name=name, normalized_name=normalized)
        session.add(record)
        session.flush()
    return record


def _apply_catalog_metadata(session: Session) -> tuple[int, int]:
    """Idempotently attach seed allergen/dietary-tag links. See module docstring."""
    allergen_links = 0
    for external_id, allergen_names in ALLERGEN_ASSIGNMENTS.items():
        item = _seed_menu_item(session, external_id)
        if item is None:
            continue
        for name in allergen_names:
            allergen = _get_or_create(session, Allergen, name)
            exists = session.scalar(
                select(MenuItemAllergen).where(
                    MenuItemAllergen.menu_item_id == item.id,
                    MenuItemAllergen.allergen_id == allergen.id,
                )
            )
            if exists is None:
                session.add(
                    MenuItemAllergen(
                        menu_item_id=item.id,
                        allergen_id=allergen.id,
                        source_type=ProvenanceSourceType.IMPORTED,
                    )
                )
                allergen_links += 1
            elif exists.source_type is ProvenanceSourceType.OFFICIAL:
                # Repair links created by the original seed implementation,
                # which accidentally relied on the model's official default.
                exists.source_type = ProvenanceSourceType.IMPORTED

    tag_links = 0
    for external_id, tag_names in DIETARY_TAG_ASSIGNMENTS.items():
        item = _seed_menu_item(session, external_id)
        if item is None:
            continue
        for name in tag_names:
            tag = _get_or_create(session, DietaryTag, name)
            exists = session.scalar(
                select(MenuItemDietaryTag).where(
                    MenuItemDietaryTag.menu_item_id == item.id,
                    MenuItemDietaryTag.dietary_tag_id == tag.id,
                )
            )
            if exists is None:
                session.add(
                    MenuItemDietaryTag(
                        menu_item_id=item.id,
                        dietary_tag_id=tag.id,
                        source_type=ProvenanceSourceType.IMPORTED,
                    )
                )
                tag_links += 1
            elif exists.source_type is ProvenanceSourceType.OFFICIAL:
                exists.source_type = ProvenanceSourceType.IMPORTED

    session.flush()
    return allergen_links, tag_links


def run_seed(session: Session, service_date: date) -> SeedSummary:
    """Seed one service date's data and return the combined summary."""
    source = FixtureDiningSource(
        build_payload(service_date),
        source_name=SOURCE_NAME,
        requested_scope={"seed": True, "service_date": service_date.isoformat()},
    )
    result = run_import(session, source, build_provider(), tolerant=False)
    if result.status is not ImportStatus.COMPLETED:
        return SeedSummary(
            import_result=result,
            allergen_links_created=0,
            dietary_tag_links_created=0,
        )

    allergen_links, tag_links = _apply_catalog_metadata(session)
    return SeedSummary(
        import_result=result,
        allergen_links_created=allergen_links,
        dietary_tag_links_created=tag_links,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Seed development data via the import pipeline.")
    parser.add_argument(
        "--date",
        type=date.fromisoformat,
        default=date.today(),
        help="service date to seed offerings for (default: today)",
    )
    args = parser.parse_args(argv)

    # Imported here so DATABASE_URL is only required when actually seeding.
    from platewise_db.session import SessionLocal

    with SessionLocal() as session:
        summary = run_seed(session, args.date)
        session.commit()

    result = summary.import_result
    counters = result.counters
    print(f"Seed import {result.import_id} finished: {result.status.value}")
    print(
        f"  records: created={counters.created} updated={counters.updated} "
        f"unchanged={counters.unchanged} skipped={counters.skipped} failed={counters.failed}"
    )
    print(
        f"  nutrition: provided={counters.nutrition_provided} "
        f"calculated={counters.nutrition_calculated}"
    )
    print(
        f"  catalog metadata: allergen_links+={summary.allergen_links_created} "
        f"dietary_tag_links+={summary.dietary_tag_links_created}"
    )
    if result.status is not ImportStatus.COMPLETED:
        print(
            f"  WARNING: run ended {result.status.value} with {result.error_count} error(s), "
            f"{result.warning_count} warning(s); see import_errors"
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
