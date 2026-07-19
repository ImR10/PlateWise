# PlateWise Data Import Architecture

This document describes the implemented data-import foundation
(`mvp/data-import-foundation`). It follows the plan of record
[docs/mvp-data-import-plan.md](mvp-data-import-plan.md) and the approved
[docs/data-import-audit.md](data-import-audit.md).

Related docs: [recipe-nutrition-calculation.md](recipe-nutrition-calculation.md),
[supported-units.md](supported-units.md), [database.md](database.md).

## Goals

Collect usable menu + nutrition data from institutions that provide it in two
shapes, converging both into one normalized model:

1. **Source-provided nutrition** — the source already gives serving info and
   nutrient values.
2. **Recipe-based nutrition** — the source gives a recipe; PlateWise calculates
   nutrition from ingredients, quantities, units, and yield.

Guiding rule: *preserve source facts, calculate only from traceable inputs,
expose uncertainty honestly, and never present invented values as authoritative.*

## Package layout (`apps/api/app/imports/`)

```
imports/
├── contracts.py        # source-neutral Pydantic DTOs (ImportPayload, ImportedMenuItem, ...)
├── enums.py            # RecordClassification, NUTRIENT_FIELDS
├── exceptions.py       # typed pipeline errors
├── decimal_utils.py    # Decimal precision + rounding policy
├── normalizers.py      # name normalization + content hashing
├── classifiers.py      # nutrition_ready / recipe_ready / incomplete / invalid
├── provenance.py       # source-vs-calculated discrepancy detection
├── repositories.py     # idempotent persistence (the only DB writer)
├── service.py          # orchestration + transaction boundary + run/error tracking
├── sources/
│   ├── base.py         # DiningSource protocol, FetchResult, per-record parse results
│   └── fixture.py      # FixtureDiningSource (the only MVP source)
├── nutrition/
│   ├── provider.py     # IngredientNutritionProvider protocol + FakeIngredientNutritionProvider
│   └── normalizer.py   # source-provided nutrition normalization
└── recipes/
    ├── units.py        # supported units + mass→gram conversion
    ├── parser.py       # ingredient-line parsing
    ├── resolver.py     # parsed line → provider food + grams + resolution status
    └── calculator.py   # Decimal aggregation → per-serving nutrition + status
```

## Two boundaries, kept separate

* **Dining-data source** (`sources/`) — where menus/recipes come from. Returns
  source-neutral contracts + the preserved raw payload. Source-specific
  structures never leak past this layer.
* **Ingredient-nutrition provider** (`nutrition/provider.py`) — where canonical
  food nutrient composition comes from. A synchronous `Protocol`; the MVP ships
  **only** a deterministic `FakeIngredientNutritionProvider`. No real external
  API, credentials, or network dependency is integrated.

Both are `Protocol`s so a future network-backed implementation slots in without
touching the pipeline. Everything is **synchronous**, matching the rest of the
app.

The service wraps the provider in a small **run-scoped lookup cache**. Repeated
deterministic ID or normalized-name lookups within one run call the underlying
provider once per unique key. Persisted provider-food rows are immutable
snapshots in the MVP: an existing `(provider, provider_food_id)` is reused rather
than rewritten, because mutating it would change the historical meaning of old
calculations. A future real provider needs an explicit snapshot/version policy.

## Flow

```
DiningSource.fetch()                     # validate + preserve raw payload (outside domain txn)
        ↓  source-neutral contracts
upsert institution → create DataImport run (status=running)
        ↓
upsert venues, stations
        ↓  for each menu item:
classify → [nutrition_ready | recipe_ready | incomplete | invalid]
        ↓  (each item inside its own SAVEPOINT)
   Path A: provided nutrition → normalize → upsert (provenance=source_provided)
   Path B: recipe → parse → resolve (provider) → convert to grams
                  → calculate per-serving (Decimal) → upsert (provenance=recipe_calculated)
        ↓
finalize run: counters + status (completed | completed_with_errors | failed)
```

### Classification

* `nutrition_ready` — usable provided nutrition (serving basis + ≥1 nutrient).
* `recipe_ready` — recipe with ingredients, positive servings, and ≥1 line
  carrying quantity+unit.
* `incomplete` — partial data (missing serving basis, missing yield, bare item).
  Preserved and flagged; never invented.
* `invalid` — structurally unusable (e.g. blank name) or a record that failed
  contract validation at the source boundary. Logged and skipped.

An item may carry **both** provided nutrition and a recipe; both paths run.

## Provenance & coexistence

`nutrition_facts.provenance` (`source_provided` / `recipe_calculated` /
`manually_entered` / `estimated`) is the coexistence discriminator. At most one
*active* row exists per `(menu_item_id, provenance)`, so the two origins never
overwrite each other. Display precedence (`MenuItem.display_nutrition()`):

1. active **source-provided** nutrition, else
2. active **recipe-calculated** nutrition **only if complete**, else
3. `None` (no authoritative nutrition).

When both exist and are complete, a large calorie discrepancy (>25%) is recorded
as a review warning (no review UI is built).

## Idempotency & identity

Re-importing identical source data creates no duplicates. Identity is
deterministic:

| Entity | Primary key (upsert) | Fallback |
| --- | --- | --- |
| institution | `(source_system, external_id)` | `slug` |
| venue | `(institution_id, source_system, external_id)` | `(institution_id, slug)` |
| station | `(venue_id, source_system, external_id)` | `(venue_id, slug)` |
| menu item | `(institution_id, source_system, external_id)` | *(none — names are not keys)* |
| ingredient | `(institution_id, source_system, external_id)` | `(institution_id, normalized_name)` |
| offering | `(station_id, source_system, external_id)` | slot `(station, item, date, meal, starts_at)` |
| provider food | `(provider, provider_food_id)` | — |
| source nutrition | active `(menu_item, source_provided)` | `content_hash` (unchanged vs versioned) |
| recipe version | active per `menu_item` | `content_hash` (unchanged vs new version) |
| calculated nutrition | active `(menu_item, recipe_calculated)` tied to active recipe version | — |

`content_hash` (SHA-256 over meaningful normalized fields) distinguishes
"unchanged" from "changed". Menu items **without** an external id are created
fresh each import — names are never an authoritative persistence key (two
distinct items may share a name); this is the documented, limited fallback.

## Transaction & safety behavior

* `source.fetch()` runs before the domain writes; the raw payload is preserved on
  `data_imports.raw_payload` (JSONB).
* Each menu-item record is processed inside its **own savepoint**
  (`session.begin_nested()`). A record failure rolls back only that record's
  writes; the run and its structured `import_errors` persist, and other records
  continue (tolerant mode). `tolerant=False` aborts on the first record failure,
  rolls back all hierarchy and domain writes from that run, and persists one
  minimal `failed` run plus a safe structured error in the caller transaction.
* The importer **only upserts — it never deletes.** An empty or malformed
  source response is therefore inherently non-destructive; existing data is
  untouched. An unscoped empty fixture response is recorded as the structured
  warning `suspiciously_empty_payload`, so it completes with review visibility
  rather than appearing clean.
* Missing nutrients stay `NULL`; unresolved ingredients contribute nothing (never
  zero); incomplete calculated nutrition is flagged (`is_complete=false`,
  `review_status=needs_review`) and excluded from authoritative display.

## Import-run tracking

Each run is one `data_imports` row: source, institution, timestamps, status,
`raw_payload` + `requested_scope` (JSONB), and counters — received / created /
updated / unchanged / skipped / failed, ingredients resolved / unresolved,
nutrition provided / calculated. Structured warnings and errors are normalized
into `import_errors` (severity, stage, code, message, source/menu-item/ingredient
context, JSONB detail), linked to the run.

Run status maps to plan outcomes: `completed` (clean), `completed_with_errors`
(succeeded with skipped/review records — covers the plan's *partial* and
*completed_with_errors*), `failed` (fatal/non-tolerant abort).

The service also emits standard Python log records with stable event names:
`import_run_started`, `import_run_completed`, `import_run_fetch_failed`,
`import_record_failed`, `import_run_rolled_back`,
`import_recipe_calculation_incomplete`, and
`import_nutrition_discrepancy`. Structured fields include safe source/run/record
references, counters, stage/code, and duration. Raw payloads, provider payloads,
full malformed records, exception text, and ingredient text are not logged.

## Input hardening

The fixture adapter validates the top-level envelope before copying or writing:

* raw JSON: at most 5 MB and 30 nested levels;
* at most 10,000 menu-item records and 5,000 venue/station records each;
* at most 500 ingredient lines per recipe;
* bounded source identifiers, names, units, ingredient text, descriptions, and
  recipe source text;
* one `source_system` namespace per run and no duplicate non-null menu-item
  source identity within a payload;
* finite, non-negative, SQL-compatible nutrient/quantity values; positive
  provider reference and portion gram weights.

Zero servings remains representable so the calculator can persist an explicit
`failed` calculation. Negative servings and ingredient quantities fail contract
validation. Provider fixtures reject duplicate IDs, ambiguous normalized
names/aliases, conflicting provider names, and duplicate normalized portion
descriptions.

## Extending the importer

* **New dining source:** implement `DiningSource` (`source_type`, `source_name`,
  `fetch() -> FetchResult`) in `sources/`. Emit source-neutral contracts and
  isolate per-record parse failures as `MenuItemParseError`. Nothing else
  changes.
* **Real ingredient-nutrition provider:** implement
  `IngredientNutritionProvider` (`get_food`, `search_food`) in
  `nutrition/provider.py`. Persist results through `upsert_provider_food` so
  calculations stay reproducible. Keep deterministic matching authoritative — an
  LLM/fuzzy result must never be used as a persistence key.

## Testing

Run against the dedicated `*_test` database (see [database.md](database.md)):

```bash
export TEST_DATABASE_URL="postgresql+psycopg://platewise:platewise_dev_password@localhost:5432/platewise_test"
pytest                      # full suite
pytest tests/test_import_service.py   # importer end-to-end
ruff check app alembic tests
```

Fixtures live in `tests/import_fixtures.py` (the 10 plan fixtures + a
deterministic fake provider). Importer tests cover classification, unit/portion
conversion, parsing, resolution, Decimal aggregation & rounding, provenance
coexistence & precedence, incomplete/review states, structured errors, tolerant
per-record rollback, non-tolerant full-run rollback, input limits,
source-identity conflicts, safe logging, provider lookup caching, and idempotency.
