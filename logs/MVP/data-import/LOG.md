# MVP — Data Import Foundation — LOG

Milestone: **Data Import Foundation** (`mvp/data-import-foundation`). Append new
entries at the bottom; do not rewrite history. Same tone/structure as
`logs/MVP/database/LOG.md`.

Plan of record: `docs/mvp-data-import-plan.md`.

---

## 2026-07-18 16:28 EDT — Phase 1: database & repository audit

### Phase / milestone

Phase 1 (audit only). No models, migrations, services, or tests modified.

### Summary

Audited the implemented M1 database against the data-import plan's requirements
and produced `docs/data-import-audit.md`. The existing schema supports the
service hierarchy, institution-scoped catalog, source-provided nutrition (with a
provenance enum), ingredient links, allergens/dietary tags, and an
`data_imports` table with raw-payload JSONB and per-run counters. It does **not**
yet support the recipe→nutrition path, cannot hold source-provided and
recipe-calculated nutrition simultaneously, and lacks canonical/provider food
storage, record classification, richer import counters/structured errors, and
multi-source identity. A migration is required for Phase 2.

### Files created

- `docs/data-import-audit.md` — full Phase 1 audit (15 required sections).
- `logs/MVP/data-import/LOG.md` — this log.

### Files modified

- None. (Audit phase; code untouched by design.)

### Schema and migration changes

- None made. Proposed for Phase 2 (pending approval): new tables
  `recipe_versions`, `recipe_ingredients`, `provider_foods`,
  `provider_food_portions`, `import_errors`; alterations to `nutrition_facts`
  (active-row uniqueness per `(item, provenance)` + calc-provenance columns) and
  `data_imports` (counters, `requested_scope`, outcome); optional `source_system`
  identity columns across the hierarchy.

### Important findings / decisions

- **Blocking gap:** `uq_nutrition_facts_active_per_menu_item` keys on
  `menu_item_id` only, so source-provided and recipe-calculated nutrition cannot
  both be active — must be relaxed to include provenance.
- **Recipe modeling absent:** only a flat `menu_item_ingredients` link exists; no
  recipe versions, yield, ingredient-line resolution, grams, or match provenance.
- **No provider layer or storage:** need a `Protocol` + deterministic fake plus
  `provider_foods`/`provider_food_portions` cache tables.
- **Decimal hazard:** `Numeric` columns are typed `Mapped[float]`; calculation
  code must use `Decimal` with an explicit rounding policy.
- **Repo conventions:** sync SQLAlchemy, Pydantic v2, Ruff (no type checker), PG
  integration tests with transactional rollback + factories; no service/repo/async
  layer yet.

### Assumptions

- `docs/mvp-data-import-plan.md` is the plan referred to as `PLAN.md` (no file
  literally named `PLAN.md` exists). Flagged for confirmation.
- MVP ships only a deterministic fake ingredient-nutrition provider (no real
  external integration) — pending confirmation.

### Deviations from PLAN.md

- None yet (no implementation). Deviations, if any, will be recorded per-change
  in Phase 2.

### Tests run

- None (audit phase). Existing suite state unchanged from the M1 milestone
  (51 passing at that time).

### Validation results

- N/A for the audit. Repository facts were read directly from source, models,
  the migration, `docs/database.md`, and the architecture report.

### Known limitations / follow-up

- Eight owner decisions (audit §14) gate Phase 2, notably multi-source identity,
  the nutrition coexistence key, recipe table modeling, provider-food storage,
  import-error normalization, sync-vs-async, and the Decimal policy.
- Awaiting explicit approval before any schema or code changes.

---

## 2026-07-18 17:23 EDT — Phase 2: implementation

### Phase / milestone

Phase 2 (implementation). Audit approved with owner decisions A–H. Both import
paths (source-provided nutrition; recipe→calculated nutrition) implemented and
validated end to end against PostgreSQL 17.

### Implementation summary

- **Schema (migration `20260718_0002`, additive on `20260718_0001`):** new tables
  `recipe_versions`, `recipe_ingredients`, `provider_foods`,
  `provider_food_portions`, `import_errors`; `nutrition_facts` gained
  `provenance` (+ coexistence index change), `is_complete`, `review_status`,
  `calculation_status`, `calculation_version`, `calculated_at`,
  `recipe_version_id`; `data_imports` gained `requested_scope` + 6 counters;
  `source_system` added to institutions/venues/stations/menu_items/ingredients/
  menu_offerings/recipe_versions with `(parent, source_system, external_id)`
  partial uniques; 8 new enums. Calc-critical columns are `Numeric`/`Decimal`.
- **Importer (`app/imports/`):** source-neutral contracts, classification,
  source-nutrition normalization, recipe parser/units/resolver/calculator,
  `IngredientNutritionProvider` protocol + deterministic fake, idempotent
  repositories, and an orchestrating service with per-record savepoints and
  run/error tracking. Synchronous throughout; `Decimal` end to end.

### Files created

- Models: `app/db/models/recipes.py`, `app/db/models/providers.py`; extended
  `app/db/models/imports.py` (`DataImportError`).
- Migration: `alembic/versions/20260718_0002_data_import_foundation.py`.
- Importer: `app/imports/{__init__,contracts,enums,exceptions,decimal_utils,
  normalizers,classifiers,provenance,repositories,service}.py`,
  `app/imports/sources/{base,fixture}.py`,
  `app/imports/nutrition/{provider,normalizer}.py`,
  `app/imports/recipes/{units,parser,resolver,calculator}.py`.
- Tests: `tests/import_fixtures.py`, `tests/test_import_units.py`,
  `tests/test_import_classification.py`, `tests/test_import_calculation.py`,
  `tests/test_import_service.py`.
- Docs: `docs/data-import-architecture.md`,
  `docs/recipe-nutrition-calculation.md`, `docs/supported-units.md`.

### Files modified

- `app/db/models/{catalog,institution,location,menu,imports,__init__}.py`,
  `app/db/enums.py` (8 enums).
- `tests/test_db_schema.py` (EXPECTED_TABLES/ENUMS + head → `20260718_0002`),
  `tests/test_db_relationships.py` (nutrition now uses `display_nutrition()` /
  `active_nutrition`).
- `docs/database.md`, `docs/data-import-audit.md` (Phase 2 status note).

### Schema / migration changes

See above. Migration is additive (no drops), safe on non-empty databases
(server-default backfill for `source_system`; documented caveat about unique
partial indexes on previously-non-unique external ids), and its `downgrade()`
drops the 8 new enum types. Verified: empty→head, head→0001→head, head→base→head,
and `alembic check` reports no drift.

### Important decisions

- Applied owner decisions A–H verbatim. Nutrition coexistence keyed on a new
  coarse `nutrition_provenance` enum (kept `nutrition_source_type` for finer
  provenance). Recipe external `source_system`/`external_id` is provenance-only
  (indexed, **not** unique) because versions share a source recipe id — the
  original audit sketch of a unique index on it was corrected during
  implementation (would have blocked recipe versioning).
- Run status maps plan outcomes onto the existing `ImportStatus`
  (`completed_with_errors` covers *partial*/review); no enum value added.
- `ImportError` model named `DataImportError` to avoid shadowing the builtin.

### Assumptions

- MVP ships only the fake provider and the fixture dining source (decisions F/G).
- Free-text ingredient parsing is intentionally conservative (structured fields
  preferred); sophisticated NLP parsing is out of scope.

### Deviations from `docs/mvp-data-import-plan.md`

- Allergen persistence from imports is not wired in this milestone (schema
  supports it; deferred as follow-up) — nutrition paths were the milestone focus.
- No per-record `import_outcome` enum; per-record results are returned in the
  `ImportResult` and reflected via counters + `import_errors` + nutrition status.

### Tests run / validation results (exact)

- `pytest` → **99 passed, 1 warning** (pre-existing Starlette/httpx deprecation).
- `ruff check app alembic tests` → **All checks passed!**
- `alembic upgrade head` from empty → OK; `downgrade 20260718_0001` → `upgrade
  head` → OK; `downgrade base` → `upgrade head` → OK; `alembic check` → **No new
  upgrade operations detected.**
- App import: `from app.main import app` OK; `configure_mappers()` OK (no
  circular imports).
- `docker compose config` → valid.

### Known limitations / follow-up

- Import allergens/dietary tags; real ingredient-nutrition provider (behind the
  existing protocol); per-institution configurable discrepancy threshold; volume
  units without a provider portion remain unsupported by design.
- API endpoints to expose imported data (targeted menu/search) — next milestone.

### Follow-up work (recommended next milestone)

Targeted read API (venue/date/meal snapshot + catalog search) over the imported
data, then availability aggregation from community reports.

---

## 2026-07-18 19:43 EDT — Phase 3: polish audit and hardening

### Phase / milestone

Phase 3 (audit, focused implementation, validation, and documentation). No Git
operation was run. No schema or migration revision changed.

### Audit summary

Created `docs/data-import-polish-audit.md` and traced the fixture source through
contracts, classification, normalization, recipe parsing/resolution/calculation,
persistence, savepoints, run/error tracking, ORM constraints/relationships,
provider caching, Decimal policy, migrations, tests, logging, and Compose.
The approved synchronous architecture remains sound; no redesign or stop
condition was found.

### Findings by severity

- **Critical:** none.
- **High:** 3 — unbounded/non-finite numeric input; unbounded/malformed payload
  envelopes; conflicting/duplicate source identities. All fixed.
- **Medium:** 7 — source-text version hash omission; skipped discrepancy checks;
  missing operational logs; repeated provider calls; provider-cache query/
  snapshot concerns; unsafe exception/source context; non-tolerant partial
  writes. Six fixed; provider snapshot mutation/version policy deferred while
  duplicate queries were reduced.
- **Low:** 4 — public result DTO typing; invisible source/empty warnings; missing
  database-level numeric checks; provider-search ambiguity. Result/warnings fixed;
  fake ambiguity rejected; database checks and future real-provider candidate
  semantics deferred.

### Files created

- `docs/data-import-polish-audit.md` — evidence-backed Phase 3 findings,
  dispositions, coverage, and final status.
- `apps/api/tests/test_import_hardening.py` — boundary, identity, numeric,
  provider, hash, and lookup-count regression tests.

### Files modified

- `apps/api/app/imports/contracts.py`
- `apps/api/app/imports/nutrition/provider.py`
- `apps/api/app/imports/sources/fixture.py`
- `apps/api/app/imports/repositories.py`
- `apps/api/app/imports/service.py`
- `apps/api/app/imports/__init__.py`
- `apps/api/alembic/env.py`
- `apps/api/tests/test_import_service.py`
- `docs/data-import-architecture.md`
- `docs/recipe-nutrition-calculation.md`
- `docs/supported-units.md`
- `docs/database.md`
- `docs/data-import-audit.md` (Phase 3 status note only; historical body kept)
- `logs/MVP/data-import/LOG.md` (this append-only entry)

### Behavior changes

- **Behavior change:** contracts reject negative/non-finite/SQL-overflowing
  nutrients and quantities; provider reference/portion grams must be positive.
- **Behavior change:** fixture input enforces 5 MB/30-level raw JSON limits,
  collection/string bounds, top-level list shapes, one source-system namespace,
  and unique non-null item identities within a payload.
- **Behavior change:** recipe `source_text` participates in the version hash, so
  body-only changes and reversions create historical versions.
- **Behavior change:** discrepancy detection runs when source nutrition changes
  even if the recipe remains unchanged.
- **Behavior change:** `tolerant=False` rolls back the entire run's domain writes
  and persists a minimal failed run/error.
- **Behavior change:** unscoped empty fixture payloads remain non-destructive but
  produce `suspiciously_empty_payload` and `completed_with_errors`.
- **Behavior change:** malformed provider fixture configuration (duplicate IDs,
  aliases, portions, or conflicting provider identity) is rejected early.

### Behavior-preserving refactors / API ergonomics

- **Refactor with no intended behavior change:** introduced a run-scoped provider
  lookup cache and reused provider-food primary keys during ingredient
  persistence.
- **Refactor with no intended behavior change:** public results now expose an
  immutable `ImportCounters` DTO and a UUID-typed `import_id`; existing counter
  field names and `ImportStatus` values remain unchanged.
- **Refactor with no intended behavior change:** Alembic in-process logging setup
  preserves existing application loggers.

### Observability and security hardening

- **Behavior change:** stable lifecycle/failure/incomplete/discrepancy log events
  include source/run/safe-record identity, requested-scope keys, counters,
  structured stage/code, and duration.
- **Behavior change:** raw/provider payloads, full malformed records, ingredient
  text, and arbitrary exception text are excluded from logs; persistence errors
  store a safe stable message. Name-only record references are hashed.
- Source-adapter warnings are persisted as structured warnings and counted
  separately from errors in `ImportResult`.

### Performance evidence

- **Before:** two repeated ID lookups called the provider twice; two equivalent
  normalized-name lookups called it twice.
- **After:** both cases call the underlying provider once per unique key (2 → 1,
  asserted by `test_run_cache_reduces_repeated_provider_calls_from_two_to_one`).
- Provider-food rows are upserted once per unique food within an item and their
  returned PK is reused, removing the prior per-line `_provider_food_pk` query.
- No timing claim was made; deterministic call/query-elimination evidence is more
  stable for the fake provider.

### Tests added or modified

- Added 21 tests (suite total 99 → 120) covering numeric limits, NaN/Infinity,
  negative quantities, provider weights/ambiguity/duplicate portions, malformed
  top-level payloads, JSON depth, duplicate/conflicting identities, source-text
  hashes, lookup counts, zero servings, changed-source discrepancy checks,
  non-tolerant rollback/redaction, and lifecycle logging.
- Updated the empty-payload assertion for its new review-warning outcome.
- Existing assertions were not weakened; no meaningful coverage was removed.

### Documentation corrections

- Documented limits, full-run rollback, safe structured logging, suspicious
  emptiness, lookup caching, immutable provider snapshots, numeric rules, and
  current model package layout.
- Corrected the testing example to use `TEST_DATABASE_URL` with a `*_test`
  database instead of pointing `DATABASE_URL` at the development database.
- Preserved `docs/data-import-audit.md` as historical Phase 1 evidence and added
  only a clearly marked Phase 3 status note.

### Exact validation commands and results

From `apps/api` with `.venv` activated unless otherwise stated:

- `TEST_DATABASE_URL=postgresql+psycopg://platewise:platewise_dev_password@localhost:5432/platewise_test DATABASE_URL=postgresql+psycopg://platewise:platewise_dev_password@localhost:5432/platewise pytest`
  → **120 passed, 1 warning in 2.60s**. The warning is the existing
  Starlette/httpx deprecation.
- `ruff check app alembic tests` → **All checks passed!**
- `DATABASE_URL=postgresql+psycopg://platewise:platewise_dev_password@localhost:5432/platewise alembic check`
  → **No new upgrade operations detected.**
- Full suite includes `test_migration_upgrade_downgrade_roundtrip` and passed.
- `python -c "from app.main import app; from sqlalchemy.orm import configure_mappers; configure_mappers(); print(app.title)"`
  → **PlateWise API**.
- From repository root, `docker compose config` → **valid**.

An initial sandboxed run could not resolve Compose host `db` and then could not
open localhost TCP. The repository PostgreSQL service was started with
`docker compose up -d db`, and database validation was rerun with explicit
localhost URLs and approved local connectivity; the final results above passed.

### Deviations from the plan

- None. This was a focused synchronous polish pass with no new provider,
  endpoint, worker, external cache, dependency, or schema revision.

### Deferred findings / known limitations

- Provider-food cache rows remain immutable snapshots; a real provider needs an
  explicit snapshot/version refresh policy so historical calculations are not
  reinterpreted.
- Database-level checks for non-negative nutrients/grams are deferred to a
  future additive migration after all direct model writers and existing data are
  audited. Importer boundaries enforce the rule now.
- The provider Protocol still returns one match or `None`; candidate-set/
  ambiguity semantics should be designed with the first real provider. The fake
  now rejects ambiguous configuration.
- Allergen/dietary-tag import wiring and real providers remain out of scope as in
  Phase 2.

### Recommended next work

Proceed to the targeted read API (venue/date/meal snapshot and catalog search),
while keeping the real-provider snapshot and ambiguity contracts as explicit
gates before any external provider integration.
