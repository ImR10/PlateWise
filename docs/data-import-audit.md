# PlateWise Data Import Foundation — Phase 1 Audit

**Date:** 2026-07-18
**Branch:** `mvp/data-import-foundation`
**Plan of record:** `docs/mvp-data-import-plan.md` (the task refers to this as
`PLAN.md`; no file literally named `PLAN.md` exists, but the full plan content is
present in the repo at that path — see [§14](#14-explicit-questions-requiring-owner-approval)).
**Status:** Audit only (Phase 1). No models, migrations, services, or tests were
modified by this document.

> **Update (Phase 2, 2026-07-18):** the audit was approved and implemented. The
> recommended schema changes shipped in migration `20260718_0002` and the
> importer in `app/imports/`. See
> [data-import-architecture.md](data-import-architecture.md),
> [recipe-nutrition-calculation.md](recipe-nutrition-calculation.md),
> [supported-units.md](supported-units.md), and
> [logs/MVP/data-import/LOG.md](../logs/MVP/data-import/LOG.md). This audit is
> retained as the Phase 1 record.
>
> **Update (Phase 3, 2026-07-18):** a focused audit and hardening pass is
> documented in [data-import-polish-audit.md](data-import-polish-audit.md). The
> Phase 1 findings below remain historical and were not rewritten.

Legend for claim types used throughout:

- **[FACT]** — verified directly from repository files (the implemented schema
  and migration are treated as operational truth).
- **[REC]** — a recommendation from this audit.
- **[ASSUMPTION]** — something inferred, not confirmed, pending owner input.
- **[DECISION]** — an unresolved product/architecture decision requiring owner
  approval before Phase 2.

---

## 1. Executive summary

**[FACT]** PlateWise has a complete, migrated M1 database foundation: 16 tables,
15 native PostgreSQL enums, one Alembic revision (`20260718_0001`), UUID primary
keys, deterministic constraint naming, a PostgreSQL-backed test harness (51
tests passing), and documentation (`docs/database.md`,
`logs/MVP/database/LOG.md`). The API layer is a thin health/status scaffold; there
is **no service layer, repository layer, importer, provider abstraction, or async
code yet**.

**[FACT]** The existing schema already supports a meaningful subset of the
importer's needs: institution → venue → station → offering → menu-item hierarchy,
an institution-scoped catalog, source-provided nutrition with a
`source_type`/provenance enum, ingredient links with quantity/unit/prep-notes,
allergens/dietary tags, and an `data_imports` table with raw-payload JSONB and
per-run counters.

**[FACT]** However, the schema **cannot yet represent the recipe→nutrition path**
described in the plan, and it **cannot hold source-provided and recipe-calculated
nutrition simultaneously**. Specifically it lacks: recipe/recipe-version modeling,
ingredient-line resolution provenance (source text, parsed qty/unit, grams,
resolution status, provider food id, match method), any canonical/provider food
representation with per-100g nutrients and portion→gram data, a record
classification/status concept, richer import-run counters
(ingredients resolved/unresolved, nutrition provided/calculated), structured
import errors, and multi-source identity (`source_system`) with the uniqueness
needed for source-id upserts on several entities.

**[REC]** A migration **is required**. Recommended shape: one additive Alembic
revision that (a) adds new tables for recipes, recipe ingredients, and provider
foods/portions; (b) extends `nutrition_facts` and `data_imports`; (c) relaxes the
"one active nutrition row per item" index to "one active row per (item, basis)";
and (d) adds source-identity columns/constraints. No existing data needs to be
destroyed (the operational DB is empty).

**[DECISION]** Eight decisions below (§14) gate Phase 2, the largest being:
multi-source identity vs single-`external_id`, recipe table modeling, canonical
food representation, sync-vs-async for the provider boundary, and the
Decimal-precision policy.

---

## 2. Current database capabilities

**[FACT]** Verified from `apps/api/app/db/models/` and the migration. All tables
have a UUID `id` PK (`gen_random_uuid()` default), `created_at`/`updated_at`
(where the `TimestampMixin` is applied), and a deterministic naming convention.

### 2.1 Service hierarchy

| Table | PK | FKs (on delete) | Uniqueness | Source identity | Timestamps |
|---|---|---|---|---|---|
| `institutions` | uuid | — | `UNIQUE(slug)` | `external_id` (nullable, **not unique**) | created/updated, `source_updated_at`, `content_hash` |
| `venues` | uuid | `institution_id → institutions (CASCADE)` | `UNIQUE(institution_id, slug)` | `external_id` (nullable, not unique) | created/updated, source_updated_at, content_hash |
| `stations` | uuid | `venue_id → venues (CASCADE)` | `UNIQUE(venue_id, slug)` | `external_id` (nullable, not unique) | created/updated, source_updated_at, content_hash |

Lifecycle: `is_active` flag; the design prefers `is_active=false` over deletion.
`station_type` free-form string; `venue_type` enum.

### 2.2 Catalog

| Table | PK | Key FKs (on delete) | Uniqueness | Notes |
|---|---|---|---|---|
| `menu_items` | uuid | `institution_id → institutions (CASCADE)`; `created_by_import_id`/`updated_by_import_id → data_imports (SET NULL)` | **partial** `UNIQUE(institution_id, external_id) WHERE external_id IS NOT NULL`; index `(institution_id, normalized_name)` | `is_active`, `is_archived`, `default_serving_size` (Numeric 10,3), `default_serving_unit`, content_hash |
| `menu_item_aliases` | uuid | `menu_item_id → menu_items (CASCADE)` | `UNIQUE(menu_item_id, normalized_alias)` | `source_type` provenance enum |
| `nutrition_facts` | uuid | `menu_item_id → menu_items (CASCADE)`; `*_by_import_id → data_imports (SET NULL)` | **partial** `UNIQUE(menu_item_id) WHERE valid_until IS NULL` | see §4 |
| `ingredients` | uuid | `institution_id → institutions (CASCADE)` | `UNIQUE(institution_id, normalized_name)` | `external_id` (nullable, not unique), content_hash |
| `menu_item_ingredients` | uuid | `menu_item_id → menu_items (CASCADE)`; `ingredient_id → ingredients (CASCADE)` | `UNIQUE(menu_item_id, ingredient_id)` | `quantity` (Numeric 10,3), `unit`, `sort_order`, `preparation_notes`, `is_estimated` |
| `allergens` | uuid | — | `UNIQUE(normalized_name)` | global catalog |
| `menu_item_allergens` | uuid | `menu_item_id`, `allergen_id` (CASCADE) | `UNIQUE(menu_item_id, allergen_id)` | `declaration_type`, `source_type` |
| `dietary_tags` | uuid | — | `UNIQUE(normalized_name)` | global catalog |
| `menu_item_dietary_tags` | uuid | `menu_item_id`, `dietary_tag_id` (CASCADE) | `UNIQUE(menu_item_id, dietary_tag_id)` | `confidence` Numeric(3,2) + CHECK `[0,1]` |

### 2.3 Menu & community

| Table | PK | Key FKs (on delete) | Uniqueness |
|---|---|---|---|
| `menu_offerings` | uuid | `station_id → stations (CASCADE)`; `menu_item_id → menu_items (RESTRICT)`; `*_by_import_id → data_imports (SET NULL)` | `UNIQUE(station_id, menu_item_id, service_date, meal_period, starts_at)` **NULLS NOT DISTINCT**; `external_id` nullable, not unique |
| `offering_reports` | uuid | `offering_id → menu_offerings (CASCADE)`; `replacement_menu_item_id → menu_items (SET NULL)` | partial `UNIQUE(offering_id, reporter_id, report_type) WHERE moderation_status='active'` |
| `menu_item_suggestions` | uuid | `institution_id (CASCADE)`; `station_id`,`related_offering_id`,`matched_menu_item_id (SET NULL)` | index `(institution_id, status)` |

### 2.4 Ingestion

**[FACT]** `data_imports` columns: `institution_id (CASCADE)`, `source_type`
(`ImportSourceType`: fixture/json/csv/foodpro_export/nutrislice_export/manual/other),
`source_name`, `source_filename`, `source_snapshot_at`, `started_at`,
`completed_at`, `status` (`ImportStatus`:
pending/running/completed/completed_with_errors/failed),
`records_received/created/updated/unchanged/failed`, `checksum`,
`error_summary` (Text), `raw_payload_reference` (String), `raw_payload` (JSONB),
`created_at`, `updated_at`. Provenance back-refs: `menu_items` and
`menu_offerings` carry `created_by_import_id` / `updated_by_import_id`
(`nutrition_facts` also has both columns).

---

## 3. Current schema limitations

**[FACT]** Enumerated against the plan's requirements:

1. **No recipe model.** There is no `recipes`, `recipe_versions`, or
   `recipe_ingredients` table. `menu_item_ingredients` is a flat catalog link
   (menu item ↔ ingredient with an optional quantity/unit/prep note). It has no
   original source text, no parsed-vs-normalized separation, no grams conversion,
   no resolution status, no provider food id, no match method, and no recipe
   yield / serving-count / yield-units concept.
2. **No canonical/provider food representation.** `ingredients` is an
   institution-scoped name catalog only. There is nowhere to store a provider's
   food id, per-100g nutrient composition, or supported portion→gram weights.
3. **Nutrition cannot coexist by provenance.** The partial unique index
   `uq_nutrition_facts_active_per_menu_item` is on `(menu_item_id) WHERE
   valid_until IS NULL` — **independent of `source_type`** — so only one active
   nutrition row can exist per item. Source-provided and recipe-calculated
   nutrition cannot both be "active" (§4).
4. **Thin nutrition provenance.** `nutrition_facts` has `source_type`,
   `source_reference`, `is_estimated`, `valid_from/until`, and `*_by_import_id`,
   but lacks: recipe/recipe-version reference, provider identity, provider food
   ids used, calculation version, calculation status, review status, and a
   nutrient-completeness indicator.
5. **No record classification / import status per item.** Nothing captures
   `nutrition_ready` / `recipe_ready` / `incomplete` / `invalid`, nor a per-item
   or per-recipe resolution/review state. (`menu_item_suggestions` is for
   user-submitted names, not import classification.)
6. **Import-run counters incomplete.** `data_imports` lacks: requested scope,
   `records_skipped` (distinct from `unchanged`), `ingredients_resolved`,
   `ingredients_unresolved`, `nutrition_provided_count`,
   `nutrition_calculated_count`, structured warnings, and structured errors
   (`error_summary` is free Text only).
7. **Single-source identity only.** Entities carry `external_id` but **no
   `source_system`**, so the plan's `institution_id + source_system +
   source_record_id` identity cannot be expressed. `external_id` is **not
   unique** on `institutions`, `venues`, `stations`, `ingredients`, or
   `offerings` (only `menu_items` has a partial unique on it).
8. **Type hints understate precision.** Numeric columns are declared
   `Mapped[float | None]` though the SQL type is `Numeric` (SQLAlchemy returns
   `Decimal` at runtime). This is a latent correctness hazard for calculation code
   (§6, §9).

---

## 4. Nutrition-provenance analysis

**[FACT]** `nutrition_facts` today:

- Distinguishes provenance via `source_type` (`NutritionSourceType`:
  `official`, `recipe_calculated`, `usda_match`, `manual`, `estimated`). So
  "source-provided" (`official`) vs "recipe-calculated" is expressible.
- Preserves serving basis (`serving_size`, `serving_unit`), a fixed nutrient set
  (calories, protein_g, carbohydrates_g, fat_g, saturated_fat_g, fiber_g,
  sugar_g, sodium_mg, cholesterol_mg — all nullable, so **missing ≠ zero** is
  representable), `is_estimated`, `valid_from`/`valid_until` versioning, a
  `content_hash`, and import back-refs.

**[FACT]** The blocking limitation: the active-row uniqueness is per
`menu_item_id`, not per `(menu_item_id, source_type)`. Two *active* rows (one
`official`, one `recipe_calculated`) violate the index. The plan **requires both
to be preserved and not overwrite each other**, with source-provided generally
taking display precedence.

**[REC]** Change the partial unique index to `(menu_item_id, nutrition_basis)
WHERE valid_until IS NULL`, where `nutrition_basis` is either the existing
`source_type` or a new coarser `nutrition_provenance` enum
(`source_provided`, `recipe_calculated`, `manually_entered`, `estimated`). This
lets one active row per provenance coexist, keeps historical versions, and keeps
"missing stays NULL".

**[REC]** Add recipe-calculated provenance fields (nullable, only populated for
calculated rows): `recipe_version_id` (FK), `calculation_version` (str),
`calculation_status` (enum: complete / partial / failed), `review_status` (enum:
not_required / needs_review / reviewed), `is_complete` (bool), `calculated_at`.
Provider/food/quantity traceability lives on the recipe-ingredient resolutions
(§6) and is referenced by the recipe version, satisfying the plan's "every
calculated value must be traceable" rule without denormalizing provider ids onto
`nutrition_facts`.

**[DECISION]** Reuse `NutritionSourceType` as the coexistence key, or introduce a
dedicated `nutrition_provenance` enum? (Recommend the latter for clarity; keep
`source_type` for finer provenance.)

---

## 5. Idempotency analysis

The plan's identity pattern is `institution_id + source_system +
source_record_id`, with limited, explicit, institution-scoped, logged name
fallback.

**[FACT]** Current upsert readiness per entity:

| Entity | Can upsert idempotently today? | On what key |
|---|---|---|
| `institutions` | Partially | `slug` unique only. `external_id` not unique, no `source_system`. |
| `venues` | Partially | `(institution_id, slug)`. No unique external id. |
| `stations` | Partially | `(venue_id, slug)`. No unique external id. |
| `menu_items` | **Yes** (single source) | partial `(institution_id, external_id)`. No `source_system`. |
| `ingredients` | Yes (by name) | `(institution_id, normalized_name)`. |
| `menu_item_ingredients` | Yes | `(menu_item_id, ingredient_id)`. |
| `nutrition_facts` | Partially | one active row per item; cannot key by provenance (§4). |
| `menu_offerings` | **Yes** | `(station_id, menu_item_id, service_date, meal_period, starts_at)` NULLS NOT DISTINCT. |
| recipes / recipe_ingredients | **No** | tables do not exist. |
| provider foods | **No** | tables do not exist. |
| `data_imports` | N/A (append per run) | new row per execution; not upserted. |

**[FACT]** Names are **not** reliable identifiers: the design report explicitly
declines a `normalized_name` uniqueness constraint on `menu_items` (two distinct
items may share a name). So name-based matching for menu items must remain an
explicit, logged fallback only — never an authoritative persistence key.

**[REC]** To make source-id upserts uniform and multi-source-safe, add a
`source_system` column and a partial unique `(institution_id, source_system,
external_id) WHERE external_id IS NOT NULL` on `institutions` (scoped globally,
not by institution), `venues`, `stations`, `menu_items`, `ingredients`, and
`menu_offerings`. Keep the existing slug/slot uniques as the deterministic,
institution-scoped **fallback** keys. **[DECISION]** whether MVP is truly
multi-source or single-source (§14-A) determines whether `source_system` is added
now or deferred.

**[REC]** Provider foods should be keyed `(provider, provider_food_id)` unique;
recipe versions keyed `(menu_item_id, version_no)` or by source recipe id +
content hash; recipe ingredients keyed `(recipe_version_id, line_no)`.

---

## 6. Recipe-storage analysis

**[FACT]** The plan requires representing: original recipe, recipe versions, yield,
serving count, yield units, ingredient lines in source order, original ingredient
text, parsed quantity, parsed unit, normalized ingredient identity, preparation
notes, grams conversion, raw-vs-cooked form, optional ingredients, unresolved
ingredients, ingredient-resolution status, and match provenance.

**[FACT]** Current coverage: only a flat `menu_item_ingredients` link with
`quantity`, `unit`, `sort_order`, `preparation_notes`, `is_estimated`.
**Everything else in that list is absent.**

**[REC]** Introduce dedicated tables (details in §11):

- `recipes` (or fold into `recipe_versions` keyed by menu item) — holds source
  recipe identity and current-version pointer.
- `recipe_versions` — `menu_item_id`, `version_no`, `yield_quantity`,
  `yield_unit`, `servings`, `source_text`/hash, `created_by_import_id`,
  `valid_from/until` (versioning), status.
- `recipe_ingredients` — `recipe_version_id`, `line_no` (source order),
  `original_text`, `parsed_quantity` (Numeric), `parsed_unit`,
  `normalized_ingredient_name`, `ingredient_id` (nullable FK to `ingredients`),
  `provider_food_id` (nullable FK to provider foods), `grams` (Numeric, nullable),
  `raw_or_cooked` (enum, nullable), `is_optional` (bool), `preparation_notes`,
  `match_method` (enum), `resolution_status` (enum: resolved / needs_review /
  unsupported_quantity / nutrition_match_missing / yield_missing /
  excluded_non_nutritive / invalid), `confidence`/`review_status`,
  `error_detail`.

**[REC]** Keep `menu_item_ingredients` for the lightweight "what's in this dish"
catalog view (used by dietary/allergen review), OR supersede it with
`recipe_ingredients`. **[DECISION]** §14-C.

---

## 7. Ingredient-nutrition provider support

**[FACT]** The plan defines a provider boundary
(`search_food` / `get_food` / `get_nutrients`) and insists the dining-data source
and the ingredient-nutrition source stay **separate concepts**. `httpx` is
available (currently a dev dependency).

**[FACT]** No provider abstraction, and no storage for provider foods, their
per-100g nutrients, or supported portion→gram weights, exists.

**[REC]** Database boundary — add a small cache/reference layer:

- `provider_foods` — `provider` (enum/str), `provider_food_id`, `description`,
  `per_100g` nutrient columns (or a related `provider_food_nutrients` table),
  unique `(provider, provider_food_id)`.
- `provider_food_portions` — `provider_food_id`, `portion_description`,
  `gram_weight` (Numeric). Enables portion→grams conversion with traceable
  provenance instead of hard-coded density guesses.

**[REC]** Application boundary — a `Protocol` (`IngredientNutritionProvider`) in
`app/imports/nutrition/provider.py` with a deterministic **fake** implementation
for tests/fixtures. No real external provider is selected or integrated in this
milestone (plan §"Explicitly Out of Scope"). **[DECISION]** sync vs async
signature (§14-G).

---

## 8. Import-run tracking analysis

**[FACT]** `data_imports` already covers: source (`source_type`, `source_name`,
`source_filename`), institution, start/complete timestamps, status, raw payload
(JSONB `raw_payload` **and** `raw_payload_reference`), and counts for
received/created/updated/unchanged/failed, plus `checksum` and a free-text
`error_summary`.

**[FACT]** Missing vs the plan: `requested_scope`, `records_skipped` (distinct
from `unchanged`), `ingredients_resolved`, `ingredients_unresolved`,
`nutrition_provided_count`, `nutrition_calculated_count`, structured `warnings`,
and structured errors. `ImportStatus` lacks the plan's richer outcomes
(`complete_source_nutrition`, `complete_calculated_nutrition`, `partial`).

**[REC]** Extend `data_imports` with the missing integer counters and a
`requested_scope` JSONB. Add a normalized **`import_errors`** table
(`data_import_id`, `severity` enum warning/error, `stage`, `record_ref`,
`code`, `message`, `detail` JSONB) rather than overloading `error_summary`; keep
`error_summary` as a short rollup and `raw_payload` for reproducibility.

**[REC]** Extend `ImportStatus` (or add an `import_outcome` enum) to carry
`partial` / `completed_with_errors` semantics without conflating server-level
failure with per-record review needs. **[DECISION]** §14-E (normalized errors vs
JSON) and enum-vs-new-column for outcomes.

---

## 9. Transaction and safety analysis

**[FACT]** `app/db/session.py` uses a **synchronous** engine + `sessionmaker`
(`autoflush=False`, `expire_on_commit=False`); `get_db()` yields a session in a
`with` block. No importer, sync-delete, or transaction helper exists yet, so
there is currently **no destructive-sync path** in the codebase.

**[FACT]** FK/delete ordering is well-defined: ownership edges `CASCADE`;
`menu_offerings → menu_items` is `RESTRICT` (catalog items can't be deleted out
from under offerings); provenance/soft refs `SET NULL`. PostgreSQL-specific
behavior is used intentionally and documented: `gen_random_uuid()`, native
enums, partial unique indexes, `NULLS NOT DISTINCT`, JSONB. Migration
upgrade→downgrade→re-upgrade is proven by tests.

**[REC]** For Phase 2, adopt the plan's flow: fetch + validate + preserve raw
payload **outside** the transaction; then a single transaction that upserts
hierarchy → catalog → recipes/resolutions → nutrition → offerings → finalizes the
run. Enforce these safety invariants (and test them):

- An empty/suspicious source response must **not** delete existing rows
  (no implicit "sync = delete missing"; offerings expire by date, not by absence).
- A per-record failure in tolerant mode is skipped + logged; a source-level or
  transactional failure aborts and rolls back, leaving no partial writes.
- Missing nutrients stay `NULL`; unresolved ingredients contribute **nothing**
  (row not counted as zero), and the recipe's nutrition is marked `partial`.

---

## 10. Recommended internal boundaries

**[REC]** Follow the plan's package layout under `apps/api/app/imports/`, adapted
to repo conventions (sync persistence, Pydantic v2 contracts, `Protocol`-based
provider). Boundaries:

- `sources/` — dining-data **source adapters** (raw records in, source-neutral
  contracts out). Source-specific JSON/CSV must not leak past this layer.
- `contracts.py` — Pydantic v2 `Imported*` DTOs (source-neutral).
- `classifiers.py` — nutrition_ready / recipe_ready / incomplete / invalid.
- `normalizers.py` + `nutrition/normalizer.py` — provided-nutrition normalization.
- `recipes/parser.py`, `recipes/units.py`, `recipes/resolver.py`,
  `recipes/calculator.py` — recipe path.
- `nutrition/provider.py` — `IngredientNutritionProvider` Protocol + fake.
- `repositories.py` — idempotent persistence using the ORM (no source shapes).
- `provenance.py`, `enums.py`, `exceptions.py`, `service.py` — coordination,
  typed errors, run tracking.

Hard rule preserved from the plan: **dining-data source** and
**ingredient-nutrition provider** are separate interfaces; neither is built
around an assumed real provider.

---

## 11. Proposed schema changes (if approved)

**[REC]** One additive Alembic revision (`down_revision = 20260718_0001`). Nothing
dropped; existing data safe.

New tables:

1. `recipe_versions` — `id`, `menu_item_id → menu_items (CASCADE)`, `version_no`,
   `source_recipe_id`, `yield_quantity` Numeric, `yield_unit`, `servings`
   Numeric, `source_text`, `content_hash`, `status`, `valid_from/until`,
   `created_by_import_id`, timestamps. Unique `(menu_item_id, version_no)`;
   partial unique active per menu item.
2. `recipe_ingredients` — as in §6. FKs to `recipe_versions (CASCADE)`,
   `ingredients (SET NULL)`, `provider_foods (SET NULL)`. Unique
   `(recipe_version_id, line_no)`.
3. `provider_foods` — `id`, `provider`, `provider_food_id`, `description`,
   per-100g nutrient columns (Numeric), timestamps. Unique
   `(provider, provider_food_id)`.
4. `provider_food_portions` — `id`, `provider_food_id → provider_foods
   (CASCADE)`, `portion_description`, `gram_weight` Numeric. Unique
   `(provider_food_id, portion_description)`.
5. `import_errors` — normalized warnings/errors (§8).
6. *(optional)* `recipe_calculations` if we prefer calc metadata in its own table
   rather than columns on `nutrition_facts` (§4). **[DECISION]**

Alterations:

- `nutrition_facts`: replace the active-per-item partial unique with
  active-per-`(menu_item_id, provenance/basis)`; add nullable calc-provenance
  columns and `recipe_version_id` FK.
- `data_imports`: add counters + `requested_scope` JSONB; extend outcome enum.
- Source identity: add `source_system` (+ partial unique with `external_id`) to
  `institutions`/`venues`/`stations`/`ingredients`/`menu_offerings` **if** §14-A
  chooses multi-source now.
- Add new enums: `resolution_status`, `match_method`, `raw_or_cooked`,
  `nutrition_provenance` (if chosen), `calculation_status`, `review_status`,
  `import_error_severity`, `provider` (or store provider as string).

**[FACT/REC]** All of this is expressible with the existing conventions
(UUID PKs, native enums, partial indexes, Numeric, JSONB) — no new extensions
required.

---

## 12. Proposed implementation sequence (Phase 2)

1. Migration + models for the new tables/columns; `alembic check`; up/down/re-up
   tests. (Gate: schema green before any importer logic.)
2. `contracts.py` + `enums.py` + `exceptions.py` (source-neutral DTOs, typed
   errors).
3. `classifiers.py` + unit tests (nutrition_ready/recipe_ready/incomplete/invalid).
4. `nutrition/normalizer.py` (provided-nutrition normalization; missing → NULL).
5. `recipes/units.py` (supported units + explicit unsupported behavior) →
   `recipes/parser.py` → `recipes/resolver.py` (against provider Protocol +
   fake) → `recipes/calculator.py` (Decimal aggregation, per-serving division,
   provenance, partial handling).
6. `nutrition/provider.py` Protocol + deterministic fake provider.
7. `repositories.py` idempotent upserts (source-id first, documented fallback).
8. `service.py` orchestration + `data_imports`/`import_errors` tracking +
   transaction boundary + non-destructive guarantees.
9. Fixtures (all 10 from the plan) + tests (classification → persistence →
   idempotency → transaction rollback → migration).
10. Docs + `logs/MVP/data-import/LOG.md` implementation entries + validation run.

---

## 13. Risks and unresolved decisions

**[FACT/REC] Risks:**

- **Nutrition coexistence index** is the highest-impact change; getting the
  active-row key wrong silently blocks the dual-nutrition requirement. Must be
  covered by an explicit constraint test.
- **Decimal vs float**: models are typed `float` over `Numeric` columns.
  Calculation code must use `Decimal` end-to-end and set an explicit
  rounding/quantization policy, or results become non-deterministic. **[REC]** fix
  the `Mapped[...]` hints to `Decimal` as part of Phase 2.
- **Portion→grams** without a trustworthy weight is unsupported by design; the
  resolver must return `unsupported_quantity`/`needs_review`, never a guess.
- **Async/sync split**: the plan shows an async provider; the repo is sync. A
  half-async design risks event-loop friction. **[DECISION]** §14-G.
- **Scope creep** into provider integrations, review dashboards, or cooking-loss
  modeling — all explicitly out of scope.

---

## 14. Explicit questions requiring owner approval

- **A. Source identity scope.** MVP single-source (keep `external_id`, defer
  `source_system`) or multi-source now (add `source_system` + partial uniques
  across the hierarchy)? *Recommendation: add `source_system` now — cheap,
  matches the plan's identity pattern, avoids a later migration.*
- **B. Nutrition coexistence key.** Relax active-per-item to active-per-`(item,
  provenance)` — confirm, and confirm source-provided display precedence.
  *Recommend yes.*
- **C. Recipe vs menu_item_ingredients.** Add dedicated `recipe_versions` +
  `recipe_ingredients` and **keep** `menu_item_ingredients` as the simple catalog
  link, or supersede it? *Recommend keep both; they serve different readers.*
- **D. Canonical food storage.** Add `provider_foods` + `provider_food_portions`
  cache tables (recommended) vs inline resolution columns only on
  `recipe_ingredients`?
- **E. Import errors.** Normalized `import_errors` table (recommended) vs JSONB on
  `data_imports` vs both?
- **F. Provider policy.** Confirm MVP ships **only** a deterministic fake/fixture
  provider (no USDA/Nutritionix/etc. network calls this milestone).
- **G. Sync vs async.** Keep the importer + provider **synchronous** to match the
  current app (recommended for MVP), or introduce async for the provider boundary
  as the plan sketches?
- **H. Decimal policy.** Approve moving nutrition/quantity code (and the
  `Mapped[...]` hints) to `Decimal` with an explicit rounding policy.

Also: **I.** the plan is at `docs/mvp-data-import-plan.md`, not `PLAN.md` — confirm
that is the intended plan of record (the task text references `PLAN.md`).

---

## 15. File-by-file implementation forecast

**[REC]** Anticipated for Phase 2 (nothing below was created/modified in Phase 1).

### Expected to CREATE

- `apps/api/alembic/versions/20260718_0002_data_import_foundation.py` — migration.
- `apps/api/app/db/models/recipes.py` — `RecipeVersion`, `RecipeIngredient`.
- `apps/api/app/db/models/providers.py` — `ProviderFood`, `ProviderFoodPortion`.
- `apps/api/app/db/models/import_errors.py` *(or fold into `imports.py`)*.
- `apps/api/app/imports/__init__.py`, `contracts.py`, `enums.py`,
  `exceptions.py`, `service.py`, `classifiers.py`, `normalizers.py`,
  `repositories.py`, `provenance.py`.
- `apps/api/app/imports/sources/__init__.py`, `base.py` (+ one fixture adapter).
- `apps/api/app/imports/recipes/parser.py`, `units.py`, `resolver.py`,
  `calculator.py`.
- `apps/api/app/imports/nutrition/provider.py`, `normalizer.py`.
- `apps/api/tests/imports/` — fixtures (the plan's 10 fixtures) + tests for
  classification, normalization, parsing, units, portion→grams, resolution,
  aggregation, per-serving, decimal/rounding, provenance, incomplete handling,
  error preservation, rollback, idempotency.
- `apps/api/tests/factories.py` additions or a new `tests/imports/factories.py`.
- `docs/data-import-architecture.md`, `docs/recipe-nutrition-calculation.md`,
  `docs/supported-units.md` (or consolidated sections).
- `logs/MVP/data-import/LOG.md` — created in Phase 1 (audit entry), appended in
  Phase 2.

### Expected to MODIFY

- `apps/api/app/db/models/catalog.py` — `nutrition_facts` provenance columns +
  active-row index change; possibly `menu_items` classification/status.
- `apps/api/app/db/models/imports.py` — new counters, `requested_scope`, outcome.
- `apps/api/app/db/models/__init__.py` — export new models.
- `apps/api/app/db/enums.py` — new enums.
- Hierarchy/catalog models — add `source_system` (+ constraints) **if** §14-A.
- `docs/database.md` — document new tables/columns.
- `apps/api/pyproject.toml` — only if a runtime dependency (e.g., promoting
  `httpx`) or a type checker is approved.
- `apps/api/tests/test_db_schema.py` — extend `EXPECTED_TABLES`/`EXPECTED_ENUMS`.

### Expected to LEAVE UNCHANGED

- `app/main.py`, `app/api/*`, `app/schemas/health.py`, `app/core/config.py`
  (unless new env vars are introduced), `session.py` (unless async is chosen),
  and all existing passing tests (they must not be weakened to pass).
