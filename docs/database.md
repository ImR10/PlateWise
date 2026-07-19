# PlateWise Database

This document describes the PlateWise database foundation (milestone **M1 —
Database Foundation**). It covers how the schema is organized, what each table
is for, how the tables relate, and the design principles behind the layout.

The authoritative design source is
[PlateWise_MVP_Database_Architecture_Report.md](PlateWise_MVP_Database_Architecture_Report.md);
this document reflects what was actually implemented. Deviations are recorded
in [logs/MVP/database/LOG.md](../logs/MVP/database/LOG.md).

## Design philosophy

The schema keeps four concerns separate rather than mixing them into a single
menu tree:

1. **Catalog** — the persistent record of *what a food is* (menu items and
   their nutrition, ingredients, allergens, dietary tags, and aliases).
2. **Service hierarchy** — *where* food is served (institutions → venues →
   stations).
3. **Menu offerings** — *where and when* a catalog item is served. An offering
   is a pointer to a catalog item, never a copy of it.
4. **Community evidence** — user reports and suggestions that provide
   *temporary* signal about a specific offering without overwriting official
   data.

The central rule:

> A menu item is stored once in the institution's catalog. A menu offering only
> holds a `menu_item_id` pointing at that catalog item.

This avoids duplication, preserves food history when an item stops being
served, and lets the same item appear at many venues, stations, dates, and meal
periods.

Supporting principles baked into the schema:

- **Institution-scoped catalog.** Menu items and ingredients belong to an
  institution; two institutions may use the same name for different recipes.
- **Persistence over deletion.** Menu items are archived (`is_archived`), not
  deleted. Venues/stations use `is_active` rather than deletion.
- **Change detection.** Ingest-facing tables carry `source_updated_at` and a
  `content_hash` so re-imports can detect *meaningful* change even when source
  timestamps are missing or unreliable.
- **Import traceability.** Catalog items and offerings record which import
  created/updated them (`created_by_import_id` / `updated_by_import_id`).
- **Reports are evidence, not edits.** `official_status` on an offering is never
  overwritten by reports; effective availability is computed separately (a later
  milestone). Database constraints enforce one active report per reporter, per
  offering, per category.

## Package organization

```
app/db/
├── base.py            # DeclarativeBase + shared MetaData (naming convention)
├── mixins.py          # UUID PK, timestamps, source-tracking column mixins
├── enums.py           # native PostgreSQL ENUM value sets + helpers
├── session.py         # engine + session factory (unchanged from scaffold)
└── models/
    ├── __init__.py    # imports every model so Base.metadata is complete
    ├── institution.py # institutions
    ├── location.py    # venues, stations
    ├── catalog.py     # menu_items, aliases, nutrition, ingredients,
    │                  #   allergens, dietary tags, and their associations
    ├── menu.py        # menu_offerings
    ├── reports.py     # offering_reports, menu_item_suggestions
    ├── imports.py     # data_imports, import_errors
    ├── providers.py   # provider_foods, provider_food_portions
    └── recipes.py     # recipe_versions, recipe_ingredients
```

Cross-module relationships use string class names and string-based
`ForeignKey("table.col")` targets, so there are no import cycles between model
modules. `app/db/models/__init__.py` imports every module, which is enough for
Alembic autogenerate and `Base.metadata.create_all` to see the whole schema.

### Conventions

- **Primary keys** are UUIDs (`gen_random_uuid()` server-side, `uuid4`
  client-side fallback), giving stable, collision-resistant identifiers
  suitable for distributed imports.
- **Timestamps** are timezone-aware; `created_at` / `updated_at` are managed by
  the database.
- **Enums** are native PostgreSQL `ENUM` types (validated at the storage layer).
  The stored value is the lowercase string, not the Python member name.
- **Constraint/index names** follow a deterministic naming convention
  (`app/db/base.py`) so migrations are reproducible.

## Tables

### Institution & service hierarchy

| Table | Purpose | Key relationships |
| --- | --- | --- |
| `institutions` | Top-level tenant (university, hospital, …). Owns the catalog and the venue hierarchy. | → venues, menu_items, ingredients, data_imports, suggestions |
| `venues` | A physical place where food is served. | institution → **venue** → stations |
| `stations` | A serving area inside a venue (Grill, Salad Bar, …). | venue → **station** → offerings |

### Catalog

| Table | Purpose | Key relationships |
| --- | --- | --- |
| `menu_items` | Persistent record of a food product / dish. | institution → **menu_item** |
| `menu_item_aliases` | Alternate names for search / import matching. | menu_item → aliases |
| `nutrition_facts` | Nutrition for an item, versioned via `valid_from`/`valid_until`. `provenance` (`source_provided`/`recipe_calculated`/…) lets source and calculated nutrition **coexist** (one active row per `(item, provenance)`); calculated rows carry `is_complete`, `review_status`, `calculation_status`, `recipe_version_id`. | menu_item → nutrition_facts; → recipe_version |
| `ingredients` | Institution-owned ingredient catalog. | institution → ingredients |
| `menu_item_ingredients` | Menu item ↔ ingredient association (quantity/unit optional). | menu_item ↔ ingredient |
| `allergens` | Normalized allergen catalog (global). | — |
| `menu_item_allergens` | Allergen declaration for an item (`contains`, `may_contain`, …). | menu_item ↔ allergen |
| `dietary_tags` | Normalized dietary-tag catalog (global). | — |
| `menu_item_dietary_tags` | Dietary tag applied to an item, with `confidence`. | menu_item ↔ dietary_tag |

### Menu

| Table | Purpose | Key relationships |
| --- | --- | --- |
| `menu_offerings` | A catalog item's placement at a station on a date/meal period. Holds `official_status`; points at the catalog via `menu_item_id`. | station → **offering** → menu_item |

### Community evidence

| Table | Purpose | Key relationships |
| --- | --- | --- |
| `offering_reports` | User observations about one offering (sold out, replacement, …). Privacy-preserving `reporter_id`. | offering → reports; report → replacement menu_item |
| `menu_item_suggestions` | Proposed items awaiting verification before entering the catalog. | institution/station/offering → suggestion → matched menu_item |

### Ingestion

| Table | Purpose | Key relationships |
| --- | --- | --- |
| `data_imports` | One ingestion run: provenance, counters (received/created/updated/unchanged/skipped/failed, ingredients resolved/unresolved, nutrition provided/calculated), `raw_payload` + `requested_scope` (JSONB). | institution → import; import → created menu_items/offerings; import → errors |
| `import_errors` | Normalized structured warnings/errors for a run (severity, stage, code, message, source/menu-item/ingredient context, JSONB detail). | data_import → errors |

### Data-import foundation (recipes & providers)

Added by migration `20260718_0002`. See
[data-import-architecture.md](data-import-architecture.md) and
[recipe-nutrition-calculation.md](recipe-nutrition-calculation.md).

| Table | Purpose | Key relationships |
| --- | --- | --- |
| `recipe_versions` | Versioned recipe (yield, servings, source text) — the calculation input. One active version per menu item; content change supersedes (history preserved). | menu_item → recipe_versions → recipe_ingredients; recipe_version → calculated nutrition |
| `recipe_ingredients` | One ingredient line of a recipe version: original text, parsed quantity/unit, grams, resolution status, match method, provider food. | recipe_version → ingredients; → ingredient (SET NULL), → provider_food (SET NULL) |
| `provider_foods` | Cached canonical food from an ingredient-nutrition provider; per-100 g nutrients + JSONB raw metadata. Unique `(provider, provider_food_id)`. | provider_food → portions |
| `provider_food_portions` | Named portion → gram weight for a provider food (portion→gram conversion). | provider_food → portions |

`recipe_versions`, `recipe_ingredients`, `provider_foods`, and
`provider_food_portions` are the recipe/calculation branch;
`menu_item_ingredients` remains the lightweight catalog-facing "what's in this
dish" link (they are not the same responsibility — see the architecture doc).

**Multi-source identity.** `institutions`, `venues`, `stations`, `menu_items`,
`ingredients`, `menu_offerings`, and `recipe_versions` carry a `source_system`
column (default `'unknown'`), giving deterministic
`(parent, source_system, external_id)` identity for idempotent imports.

## Relationship map

```text
institutions
├── venues
│   └── stations
│       └── menu_offerings ──────────────┐  (station_id, menu_item_id)
├── menu_items ◄──────────────────────── ┘
│   ├── menu_item_aliases
│   ├── nutrition_facts
│   ├── menu_item_ingredients ── ingredients
│   ├── menu_item_allergens ──── allergens        (allergens/dietary_tags
│   └── menu_item_dietary_tags ─ dietary_tags      are global catalogs)
├── ingredients
├── data_imports
│   ├── (created_by_import_id) ─ menu_items
│   └── (created_by_import_id) ─ menu_offerings
└── menu_item_suggestions

menu_offerings
└── offering_reports  (reporter_id; replacement_menu_item_id → menu_items)
```

## Foreign-key / delete behavior

| From → To | On delete | Rationale |
| --- | --- | --- |
| venues, stations, menu_items, ingredients, data_imports, suggestions → owning institution/parent | `CASCADE` | Ownership: removing a tenant/parent removes its owned rows. |
| menu_offerings → menu_items | `RESTRICT` | Catalog items are persistent; an item still referenced by an offering cannot be deleted. |
| menu_offerings → stations | `CASCADE` | Offerings belong to a station. |
| offering_reports → menu_offerings | `CASCADE` | Reports belong to an offering. |
| `*_by_import_id`, `replacement_menu_item_id`, `matched_menu_item_id`, suggestion `station_id`/`related_offering_id` | `SET NULL` | Provenance / soft references survive deletion of the referenced row. |

## Notable constraints & indexes

- `UNIQUE(institutions.slug)`, `UNIQUE(venues.institution_id, slug)`,
  `UNIQUE(stations.venue_id, slug)`.
- **Partial unique** `menu_items(institution_id, source_system, external_id)
  WHERE external_id IS NOT NULL` — external ids are unique per institution and
  source system; many items may have no external id. Equivalent
  `(parent, source_system, external_id)` partial uniques exist on institutions,
  venues, stations, and ingredients (with slug/name kept as the fallback key).
- **Partial unique** `nutrition_facts(menu_item_id, provenance) WHERE valid_until
  IS NULL` — one active nutrition version per `(item, provenance)`, so
  source-provided and recipe-calculated nutrition coexist.
- **Partial unique** `recipe_versions(menu_item_id) WHERE valid_until IS NULL` —
  one active recipe version per item.
- `CHECK` on `recipe_ingredients.confidence ∈ [0, 1]`.
- **Partial unique** `offering_reports(offering_id, reporter_id, report_type)
  WHERE moderation_status = 'active'` — one active report per reporter, per
  offering, per category (retracting frees the slot).
- `menu_offerings` slot uniqueness `(station_id, menu_item_id, service_date,
  meal_period, starts_at)` with **NULLS NOT DISTINCT** (PostgreSQL 15+) so a
  NULL `starts_at` still deduplicates on re-import.
- `CHECK` on `menu_item_dietary_tags.confidence ∈ [0, 1]`.
- Read-path indexes: `menu_items(institution_id, normalized_name)`,
  `menu_offerings(station_id, service_date, meal_period)`,
  `menu_offerings(menu_item_id, service_date)`,
  `nutrition_facts(menu_item_id, valid_from, valid_until)`, and the alias /
  ingredient / report lookup indexes from the architecture report.

## Migrations

Two Alembic revisions build the schema (21 tables, 23 enum types total):

- `20260718_0001_initial_platewise_schema.py` — the initial 16 tables / 15 enums.
- `20260718_0002_data_import_foundation.py` — additive: recipe/provider/import-error
  tables, nutrition provenance & coexistence, `source_system` identity, and extra
  import-run counters. Nothing is dropped; the migration is written to be safe on a
  non-empty database (documented in its docstring).

Each `downgrade()` also drops the enum types it created (Alembic does not do this
automatically), so upgrade→downgrade→re-upgrade cycles are clean.

```bash
# From apps/api, with DATABASE_URL pointing at your database:
alembic upgrade head      # build the schema
alembic downgrade base    # tear it down
alembic check             # verify models and migration agree (no drift)
```

## Running the tests

Database tests run against a dedicated `<db>_test` database (derived from
`DATABASE_URL`, or set `TEST_DATABASE_URL` explicitly). The schema is built by
running the real migration, and each test executes inside a rolled-back
transaction for isolation. Tests are skipped automatically if PostgreSQL is
unreachable.

```bash
# Postgres reachable on localhost:
export DATABASE_URL="postgresql+psycopg://platewise:platewise_dev_password@localhost:5432/platewise"
pytest
```
