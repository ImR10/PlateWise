# MVP — Database Foundation — LOG

Milestone: **M1, Database Foundation.** Append new entries at the bottom; do not
rewrite history.

Source of truth: `docs/PlateWise_MVP_Database_Architecture_Report.md`.

---

## 2026-07-18 04:37 EDT — Milestone implemented

### Completed work

- Added the database foundation package under `apps/api/app/db/`:
  - `base.py` — `DeclarativeBase` with a shared `MetaData` naming convention for
    deterministic constraint/index names.
  - `mixins.py` — `UUIDPrimaryKeyMixin`, `TimestampMixin`, `SourceTrackingMixin`.
  - `enums.py` — 15 native PostgreSQL enum value sets + `pg_enum` / `enum_values`
    helpers.
  - `models/` — 16 ORM models split by domain: `institution.py`, `location.py`,
    `catalog.py`, `menu.py`, `reports.py`, `imports.py`.
- Implemented all 16 MVP tables with relationships, FKs (with explicit
  `ondelete`), indexes, uniqueness constraints, enums, timestamps, a check
  constraint, type hints, and docstrings.
- Generated and hand-verified the initial Alembic migration
  `20260718_0001_initial_platewise_schema.py` (16 tables, 15 enum types, all
  indexes/constraints). Verified `upgrade → downgrade → upgrade` on an empty DB
  and `alembic check` reports no drift.
- Test suite (`apps/api/tests/`): `conftest.py` (dedicated `*_test` DB built via
  the real migration, per-test transactional rollback), `factories.py`
  (lightweight builders), and schema/relationship/constraint test modules.
  **51 tests pass** against PostgreSQL 17.10.
- Documentation: `docs/database.md` (schema org, table purposes, relationships,
  design philosophy, constraints, how to migrate/test).
- Validation: `ruff` clean, no circular imports, `app.main` imports and the
  FastAPI app starts.

### Important design decisions

- **UUID primary keys everywhere** (`gen_random_uuid()` server default, `uuid4`
  Python fallback). The report calls for stable, collision-resistant ids and
  UUIDs suit distributed/idempotent imports. (The removed `campuses` scaffold
  used integer PKs.)
- **Native PostgreSQL enums** for all fixed vocabularies, so invalid values are
  rejected at the storage layer. Each column that reuses a Python enum across
  tables gets its **own DB type name** (e.g. `alias_source_type`,
  `allergen_source_type`, `dietary_tag_source_type` all back the same
  `ProvenanceSourceType`; `import_source_type` vs `offering_source_type` back
  `ImportSourceType`). This deliberately avoids the shared-enum duplicate
  `CREATE TYPE` problem in Alembic.
- **Nutrition versioning** via `valid_from`/`valid_until` with a partial unique
  index enforcing one active row per item (report §10).
- **Report dedup at the database level** via a partial unique index
  (`… WHERE moderation_status = 'active'`), implementing the report's "one active
  report per reporter per offering per category" rule (report §22, §40).
- **Offering slot uniqueness uses `NULLS NOT DISTINCT`** (PostgreSQL 15+; we run
  17) so offerings with a NULL `starts_at` still deduplicate on re-import.
- **Serving size stored as numeric + unit** (`default_serving_size` +
  `default_serving_unit`, and the same on `nutrition_facts`) rather than a
  combined display string, keeping the data normalized.
- **Delete policy encoded in FKs**: ownership edges `CASCADE`;
  `menu_offerings → menu_items` is `RESTRICT` (catalog items persist);
  provenance/soft references (`*_by_import_id`, replacement/matched item,
  suggestion station/offering) are `SET NULL`.
- **`data_imports.raw_payload`** added as optional `JSONB` (report §31) in
  addition to `raw_payload_reference`.

### Deviations from the architecture document

1. **`campuses` scaffold removed.** The pre-existing placeholder `campuses`
   table/model and its migration (`20260716_0001_create_campuses.py`) were
   replaced by the real top-level entity, `institutions`. The initial migration
   is therefore a fresh single revision with `down_revision = None`. Safe
   because the scaffold was throwaway and the dev database is empty.
2. **Model location.** Models live in `app/db/models/` (per this milestone's
   layout spec) rather than the scaffold's `app/models/`. `alembic/env.py` now
   imports `app.db.models`.
3. **`menu_item_suggestions` included.** The report lists it as optional for the
   earliest PoC, but it is in the M1 scope list, so it was implemented.
4. **`report_type` includes `staff_confirmed`.** The report's §19 report-type
   list omits it, but §24 treats `staff_confirmed` as positive evidence, so it
   was added to the enum for forward compatibility.
5. **Extra normalized-name uniqueness on `ingredients`**
   (`UNIQUE(institution_id, normalized_name)`) to support idempotent ingredient
   imports. The report cautions against this only for `menu_items` (where it is
   intentionally *not* enforced); ingredients are a dedup-friendly catalog.
6. **Added convenience uniqueness** on `menu_item_aliases(menu_item_id,
   normalized_alias)` and on each association table (`menu_item_ingredients`,
   `menu_item_allergens`, `menu_item_dietary_tags`) to prevent duplicate links.
7. **Ruff config**: added a per-file `E501` ignore for `alembic/versions/*`,
   since autogenerated migration DDL lines exceed the 100-column limit.

### Unresolved questions / assumptions

- **`institution.timezone` default** set to `UTC`; real imports should set the
  institution's actual IANA zone (e.g. `America/New_York`).
- **`station_type`** left as free-form `String` (the report gives no fixed
  vocabulary). Revisit if real source data has a stable set.
- **`.env` naming drift** — *RESOLVED 2026-07-18 (see entry below).* The repo's
  `.env` had pre-rename database/user names while `.env.example` used
  `platewise`; this was flagged here and then fixed in the rename-audit entry.
- **`default_serving_size` / nutrition `serving_size` as numeric**: assumes
  sources provide (or can be parsed into) a numeric size + unit. A combined
  free-text serving string is not stored; confirm against real FoodPro/Nutrislice
  payloads during the importer milestone.

### Future work (explicitly out of scope for M1)

- Fixture *importer* and the shared import service layer (report Step 4).
- Targeted menu endpoint, catalog search, report storage/aggregation, effective
  availability computation (report Steps 5–8).
- Configurable report thresholds and time-decay weighting.
- Full-text / trigram indexes for catalog search.
- Optional: canonical cross-institution ingredient layer; nutrition/recipe
  version history beyond the single-active-row model; reporter reputation.

---

## 2026-07-18 04:52 EDT — Repository-wide rename audit (pre-rename name → PlateWise)

Triggered by the PostgreSQL test infrastructure: Docker was initializing the DB
with the pre-rename role/database names while the app and tests expect
`platewise`, so the `platewise` role did not exist and the migration round-trip
test failed against a Docker-provisioned database.

Performed a full repo-wide, case-insensitive audit (`unidine` / `UniDine` /
`UNIDINE`) across source, config, infra, CI, docs, and scripts.

### Files changed

- **`.env`** — the root cause. `POSTGRES_DB`, `POSTGRES_USER`,
  `POSTGRES_PASSWORD`, and `DATABASE_URL` now use `platewise` /
  `platewise_dev_password`, matching `.env.example`, `app/core/config.py`, and
  the test harness. This is what makes Docker create the correct role/database.
- **`README.md`** — `cd unidine` → `cd platewise` in the setup steps.
- **`docs/mvp-architecture.md`** — title renamed to "PlateWise MVP".
- **`docs/mvp-sequence.md`** — title and two body references renamed to
  PlateWise.
- **`logs/MVP/database/LOG.md`** — marked the earlier `.env` drift note resolved
  and added this entry.

### Verified clean (no changes needed)

`compose.yaml` and both `Dockerfile`s reference DB creds only via `${POSTGRES_*}`
env vars, so fixing `.env` fixes Docker. `alembic.ini`, `pyproject.toml`,
`app/core/config.py`, `pnpm-workspace.yaml`, all `package.json`, and the
`uv.lock` / `pnpm-lock.yaml` lockfiles contained no old-name references. No
`.github`, `.vscode`, `scripts/`, `Makefile`, `*.sh`, or `*.sql` files exist.

A repository-wide search now finds zero project-name references to the old name
(build/dependency caches excluded).
