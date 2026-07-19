# PlateWise MVP Database Architecture Report

## 1. Purpose

PlateWise needs a database architecture that supports four distinct concerns without mixing them together:

1. A persistent catalog of food items.
2. A hierarchy of institutions, venues, and food stations.
3. Time-specific menu offerings that point to catalog items.
4. Live community reports that influence availability and recommendations.

The most important architectural rule is:

> A menu item is not stored inside a venue or offering tree.  
> A menu offering only contains a pointer to a menu item stored separately in the institution's catalog.

This avoids duplication, preserves historical food records, and allows the same menu item to appear at multiple venues, stations, dates, and meal periods.

---

# 2. High-Level Architecture

```text
Institution
├── Menu Item Catalog
│   ├── Menu Items
│   │   ├── Nutrition
│   │   ├── Ingredients
│   │   ├── Allergens
│   │   ├── Dietary Tags
│   │   └── Aliases
│   └── Ingredient Catalog
│
└── Service Hierarchy
    └── Venues
        └── Stations
            └── Menu Offerings
                └── menu_item_id → Menu Item Catalog
```

The database remains one PostgreSQL database, but the data is separated into focused relational tables.

The user-facing app should never download the entire database. It should request targeted JSON responses for a specific institution, venue, date, and meal period.

---

# 3. Core Design Principles

1. Menu items are persistent catalog records.
2. Menu offerings are temporary, scheduled, or live placement records.
3. An offering references a menu item through `menu_item_id`.
4. Menu items are grouped by institution.
5. Nutrition, ingredients, allergens, and dietary tags belong to menu items or their versioned recipe data.
6. Venues and stations belong to the institution's service hierarchy.
7. Community reports never overwrite official source data.
8. One report never determines availability by itself.
9. Report influence depends on recency, agreement, independence, and report type.
10. Menu items should not be automatically deleted merely because they disappear from a menu.
11. The app downloads only the subset of data needed for the current user action.
12. Stable IDs, timestamps, source timestamps, and content hashes are used for change detection.
13. The recommendation algorithm may run on the user's device using a compact downloaded menu snapshot.

---

# 4. Why the Catalog and Menu Tree Must Be Separate

Consider the menu item:

```text
Grilled Chicken Breast
```

That item may appear at:

```text
Bolton Dining Commons → Grill → Lunch
Village Summit → Entrées → Dinner
Oglethorpe House → Hot Line → Lunch
```

These are three separate offerings that all point to the same institution-owned catalog item.

The menu item should not be duplicated three times.

Correct:

```text
Menu Item Catalog
└── Grilled Chicken Breast [menu_item_id = 42]

Offerings
├── Bolton Grill Lunch       → menu_item_id 42
├── Village Summit Dinner    → menu_item_id 42
└── Oglethorpe House Lunch   → menu_item_id 42
```

Incorrect:

```text
Bolton
└── Grilled Chicken Breast
    └── Nutrition duplicated here

Village Summit
└── Grilled Chicken Breast
    └── Nutrition duplicated again
```

The separate catalog model ensures that changes to the item's nutrition, ingredients, or aliases do not require editing every menu placement.

---

# 5. Database Technology

## Recommended Database

Use one PostgreSQL 17 database as the canonical source of truth.

```text
platewise
```

Use:

- PostgreSQL for canonical relational data
- SQLAlchemy 2.x for backend models
- Alembic for migrations
- JSON or CSV for import payloads and fixtures
- JSON API responses for user devices
- Optional JSONB columns for preserving raw source records

Do not use separate physical databases for menu items, venues, offerings, or reports during the MVP.

Separate tables provide the needed organization while preserving:

- foreign keys
- joins
- transactions
- constraints
- migrations
- backups
- consistent IDs

---

# 6. Institution Table

An institution is the top-level organization that owns both the food catalog and the venue hierarchy.

Examples:

- University of Georgia
- Georgia Tech
- Northside Hospital
- A corporate campus
- A senior-living facility

## Table: `institutions`

```text
id
name
slug
institution_type
timezone
external_id
is_active
created_at
updated_at
source_updated_at
content_hash
```

## Suggested institution types

```text
university
hospital
corporate_campus
senior_living
government
other
```

## Notes

- `id` is PlateWise's stable internal identifier.
- `external_id` stores an identifier from FoodPro, Nutrislice, or another source when available.
- `source_updated_at` is the source system's update timestamp, if provided.
- `content_hash` helps detect meaningful data changes even when source timestamps are missing or unreliable.

---

# 7. Institution-Owned Menu Item Catalog

Every institution has its own menu-item catalog.

```text
Institution
└── Menu Item Catalog
```

For the MVP, menu items should be institution-specific because two institutions may use the same name for foods with different recipes, portions, ingredients, or nutrition.

Example:

```text
University of Georgia
├── Grilled Chicken Breast
├── Turkey Burger
├── Brown Rice
├── Broccoli
└── Macaroni and Cheese
```

These records remain searchable even when they are not being served currently.

---

# 8. Menu Items

A menu item represents a food product or prepared dish.

## Table: `menu_items`

```text
id
institution_id
external_id

name
normalized_name
description

default_serving_size
default_serving_unit

is_active
is_archived

created_at
updated_at
source_updated_at

content_hash
created_by_import_id
updated_by_import_id
```

## Field meanings

### `id`

Stable PlateWise identifier.

Use UUIDs or another collision-resistant stable identifier.

### `institution_id`

Foreign key to the institution that owns the item.

### `external_id`

Official source identifier when available.

### `normalized_name`

Search-friendly normalized form.

Example:

```text
Display: Grilled Chicken Breast
Normalized: grilled chicken breast
```

### `is_active`

Indicates that the institution may still serve the item.

This should not be set to false merely because the item is absent from today's menu.

### `is_archived`

Reserved for:

- duplicate records
- invalid records
- manually retired items
- data-cleanup cases

Archived items can remain in history without appearing in ordinary search results.

### `content_hash`

Fingerprint of meaningful fields used for change detection.

---

# 9. Menu Item Aliases

Menu items may be known by multiple names.

Examples:

```text
Macaroni and Cheese
Mac & Cheese
Mac n Cheese
Baked Macaroni
```

## Table: `menu_item_aliases`

```text
id
menu_item_id
alias
normalized_alias
source_type
created_at
```

## Suggested source types

```text
official
imported
user_suggested
manually_verified
```

Aliases improve:

- search
- import matching
- duplicate detection
- user reporting
- menu-item replacement matching

---

# 10. Nutrition Data

Nutrition belongs to the catalog item or, when needed, a versioned recipe record.

For the first MVP, a direct menu-item nutrition table is acceptable.

## Table: `nutrition_facts`

```text
id
menu_item_id

serving_size
serving_unit

calories
protein_g
carbohydrates_g
fat_g
saturated_fat_g
fiber_g
sugar_g
sodium_mg
cholesterol_mg

source_type
source_reference
is_estimated

valid_from
valid_until

created_at
updated_at
source_updated_at
content_hash

created_by_import_id
updated_by_import_id
```

## Suggested source types

```text
official
recipe_calculated
usda_match
manual
estimated
```

## Versioning

Nutrition can change when:

- a recipe changes
- serving size changes
- the institution updates data
- an incorrect value is corrected

Instead of overwriting historical values forever, nutrition records may use:

```text
valid_from
valid_until
```

For the MVP, PlateWise can maintain one active nutrition record per menu item and preserve previous versions when a meaningful change occurs.

---

# 11. Ingredient Catalog

Ingredients should exist in their own searchable catalog.

## Table: `ingredients`

```text
id
institution_id
external_id

name
normalized_name
description

created_at
updated_at
source_updated_at
content_hash
```

Ingredients may be institution-owned initially because local naming and product usage can vary.

A future canonical ingredient layer may be added later for USDA or cross-institution matching.

---

# 12. Menu Item to Ingredient Relationship

Menu items and ingredients form a many-to-many relationship.

## Table: `menu_item_ingredients`

```text
id
menu_item_id
ingredient_id

quantity
unit
sort_order
preparation_notes

is_estimated

created_at
updated_at
```

Quantity and unit may be null when an institution only provides an ingredient list without recipe amounts.

Example:

```text
Grilled Chicken Breast
├── Chicken breast
├── Olive oil
├── Salt
├── Black pepper
└── Garlic
```

This relationship remains useful even without quantities because it supports:

- ingredient search
- allergen review
- dietary filtering
- substitution reasoning
- recipe comparison

---

# 13. Allergens

Allergens should be normalized into a catalog rather than stored as arbitrary text.

## Table: `allergens`

```text
id
name
normalized_name
created_at
updated_at
```

Examples:

```text
milk
egg
peanut
tree_nut
soy
wheat
fish
shellfish
sesame
```

## Table: `menu_item_allergens`

```text
id
menu_item_id
allergen_id
declaration_type
source_type
created_at
updated_at
```

## Suggested declaration types

```text
contains
may_contain
facility_warning
unknown
```

Important rule:

> The absence of a listed allergen must not automatically be interpreted as allergen-free.

---

# 14. Dietary Tags

Dietary tags should also use a normalized many-to-many structure.

## Table: `dietary_tags`

```text
id
name
normalized_name
created_at
updated_at
```

Examples:

```text
vegetarian
vegan
halal
kosher
gluten_free
dairy_free
```

## Table: `menu_item_dietary_tags`

```text
id
menu_item_id
dietary_tag_id
source_type
confidence
created_at
updated_at
```

A confidence field allows PlateWise to distinguish official tags from inferred or user-suggested tags.

---

# 15. Venues

A venue is a physical place where food is served.

Examples:

- dining hall
- cafeteria
- café
- food court
- restaurant
- hospital cafeteria

## Table: `venues`

```text
id
institution_id
external_id

name
slug
venue_type
description

is_active

created_at
updated_at
source_updated_at
content_hash
```

## Suggested venue types

```text
dining_hall
cafeteria
cafe
food_court
restaurant
other
```

---

# 16. Stations

A station is an individual serving area inside a venue.

Examples:

- Grill
- Pizza
- Salad Bar
- International
- Desserts
- Hot Entrées
- Made to Order

## Table: `stations`

```text
id
venue_id
external_id

name
slug
station_type
description

is_active

created_at
updated_at
source_updated_at
content_hash
```

A station should not be automatically deleted because it disappears from one import.

It may instead be marked inactive after confirmed long-term removal or manual review.

---

# 17. Menu Offerings

A menu offering represents a menu item's placement at a specific station and time.

It is not the food itself.

## Table: `menu_offerings`

```text
id

station_id
menu_item_id

service_date
meal_period

starts_at
ends_at

official_status
source_type
external_id

created_at
updated_at
source_updated_at
content_hash

created_by_import_id
updated_by_import_id
```

## Critical relationship

```text
menu_offerings.menu_item_id
    → menu_items.id
```

The offering points to the catalog item.

## Suggested meal periods

```text
breakfast
brunch
lunch
dinner
late_night
all_day
other
```

## Suggested official statuses

```text
scheduled
available
unavailable
cancelled
unknown
```

Community-derived availability should not overwrite `official_status`. It should be calculated separately from reports.

---

# 18. Persistent Catalog vs Temporary Offering

The permanent catalog answers:

> What is this food?

The offering answers:

> Where and when is this food being served?

Example:

```text
Catalog item:
Grilled Chicken Breast

Offerings:
- Bolton → Grill → July 18 lunch
- Oglethorpe House → Hot Entrées → July 18 dinner
- Village Summit → Grill → July 19 lunch
```

If one offering becomes unavailable, the catalog item and other offerings remain unaffected.

---

# 19. Community Reports

Official menu data may not reflect live conditions.

Foods may:

- sell out
- be replaced
- move stations
- appear unexpectedly
- return after being restocked
- be incorrectly listed

Community reports should be stored as evidence, not as direct edits to official records.

## Table: `offering_reports`

```text
id

offering_id
reporter_id

report_type
replacement_menu_item_id

notes
reported_at
retracted_at

moderation_status
created_at
updated_at
```

## Suggested report types

```text
sold_out
not_present
replacement
available_now
back_in_stock
wrong_station
wrong_item
wrong_nutrition
other
```

## Suggested moderation statuses

```text
active
retracted
flagged
rejected
confirmed
```

---

# 20. Reports Must Attach to Offerings

Incorrect:

```text
Grilled Chicken Breast
└── sold out
```

Correct:

```text
Bolton
└── Grill
    └── July 18 lunch offering
        └── sold out report
```

The same food may still be available elsewhere.

Reports therefore attach to:

```text
institution + venue + station + date + meal period + menu item
```

through the offering record.

---

# 21. One Report Must Not Control Recommendations

A single report should never remove a dish from recommendations.

PlateWise should aggregate independent, recent reports.

## Initial MVP policy

| Independent recent reports | Recommendation behavior |
|---:|---|
| 0 | Recommend normally |
| 1 | Keep normal ranking; optionally show an informational notice |
| 2 | Apply a small ranking penalty and show possible uncertainty |
| 3 | Apply a strong ranking penalty and show a prominent warning |
| 4 or more | Exclude from default recommendations when reports are sufficiently recent and not contradicted |

The item should remain:

- searchable
- visible when the user requests unavailable items
- visible with an explanation
- recoverable through newer positive reports

The threshold must be configurable rather than scattered as hard-coded constants.

---

# 22. Report Independence and Deduplication

Reports must be counted by independent reporters.

One user or device pressing a button repeatedly should not generate multiple votes.

Recommended rule:

```text
One active report per reporter
per offering
per report category
within the active report window
```

A reporter may:

- change their report
- retract it
- replace it with a newer status

Possible reporter identities:

- authenticated user ID
- privacy-preserving installation ID
- institution staff ID
- verified moderator ID

---

# 23. Report Recency and Expiration

Different reports need different lifetimes.

Suggested starting windows:

```text
sold_out: 60 minutes
not_present: 60 minutes
available_now: 30 minutes
back_in_stock: 30 minutes
replacement: until meal period ends
wrong_station: until meal period ends
wrong_nutrition: persistent until reviewed
```

Reports should gradually lose influence over time.

Example weighting:

```text
0–15 minutes old: 100% influence
15–30 minutes: 75%
30–45 minutes: 50%
45–60 minutes: 25%
after 60 minutes: ignored for live availability
```

These values should be configurable and tested with real usage.

---

# 24. Positive and Negative Evidence

PlateWise should consider both negative and positive reports.

Negative evidence:

```text
sold_out
not_present
replacement
```

Positive evidence:

```text
available_now
back_in_stock
staff_confirmed
```

Example:

```text
4 sold-out reports from 45 minutes ago
2 available-now reports from 5 minutes ago
```

The newer positive reports may restore the item to recommendations.

The algorithm should evaluate:

```text
official baseline
+ weighted positive reports
- weighted negative reports
= effective availability confidence
```

The exact confidence formula can evolve, but the database must retain the individual reports needed to calculate it.

---

# 25. Effective Availability

Do not permanently store a user-controlled availability value as if it were official truth.

Instead, compute or cache an effective availability state from:

- official offering status
- report count
- report recency
- reporter independence
- report agreement
- positive confirmations
- staff confirmations
- moderation status

Possible derived states:

```text
likely_available
probably_available
uncertain
possibly_unavailable
likely_unavailable
replaced
```

A cached derived state may be stored for performance, but the underlying reports remain the source evidence.

---

# 26. Replacement Reports

A user may report that one item was replaced by another.

Example:

```text
Official offering:
Turkey Burger

User-observed replacement:
Grilled Chicken Breast
```

The report should include:

```text
offering_id
report_type = replacement
replacement_menu_item_id
```

The replacement points to an existing catalog item.

If the replacement item does not exist in the catalog, create a suggestion rather than immediately inserting an unverified menu item.

---

# 27. Menu Item Suggestions

## Table: `menu_item_suggestions`

```text
id
institution_id
station_id
related_offering_id

proposed_name
normalized_name
description
submitted_by

status
matched_menu_item_id

created_at
updated_at
```

## Suggested statuses

```text
pending
matched
approved
rejected
duplicate
```

This prevents unverified names from immediately polluting the permanent catalog.

---

# 28. Change Detection

Timestamps alone are not always enough to determine whether source values changed.

Use:

```text
stable ID
external ID
created_at
updated_at
source_updated_at
content_hash
```

## Meaning of timestamps

### `created_at`

When PlateWise first created the record.

### `updated_at`

When PlateWise last changed the stored record.

### `source_updated_at`

When the external source says the record changed.

This may be null when the source does not provide timestamps.

### `content_hash`

A deterministic hash of meaningful normalized values.

For nutrition, the hash may include:

```text
serving size
calories
protein
carbohydrates
fat
fiber
sodium
ingredients
allergens
```

If a new import produces the same hash, the record is unchanged even if the source refreshed its timestamp.

If the hash changes, PlateWise knows that meaningful content changed.

---

# 29. Why `last_seen_at` Is Not Required for User Activity

`last_seen_at` must never mean:

```text
the last time a user viewed this item
```

User devices should not update ingestion metadata.

If used at all, `last_seen_at` would mean:

```text
the last successful source import that still contained this record
```

However, PlateWise plans to keep menu items permanently, so `last_seen_at` is not required on menu items for the MVP.

It may still be useful on volatile source records such as stations or externally scheduled offerings, but it should be added only when the importer needs disappearance detection.

---

# 30. Import Tracking

Each data import should have its own record.

## Table: `data_imports`

```text
id
institution_id

source_type
source_name
source_filename
source_snapshot_at

started_at
completed_at

status

records_received
records_created
records_updated
records_unchanged
records_failed

checksum
error_summary
raw_payload_reference
```

## Suggested source types

```text
fixture
json
csv
foodpro_export
nutrislice_export
manual
other
```

## Suggested statuses

```text
pending
running
completed
completed_with_errors
failed
```

Imports should be idempotent whenever possible.

Re-importing the same source data should not create duplicate items or offerings.

---

# 31. Raw Source Preservation

The normalized relational tables remain canonical, but raw source information may be preserved for debugging.

Possible approaches:

```text
data_imports.raw_payload JSONB
```

or:

```text
object-storage reference to original CSV/JSON export
```

Raw JSON should supplement the normalized model, not replace it.

---

# 32. Recommended Table Groups

## Catalog tables

```text
menu_items
menu_item_aliases
nutrition_facts
ingredients
menu_item_ingredients
allergens
menu_item_allergens
dietary_tags
menu_item_dietary_tags
```

## Institution and location tables

```text
institutions
venues
stations
```

## Menu tables

```text
menu_offerings
```

## Community tables

```text
offering_reports
menu_item_suggestions
```

## Ingestion tables

```text
data_imports
```

All of these can exist in one PostgreSQL database.

---

# 33. App Data Delivery

The app should never download the entire database.

Instead, the backend exposes focused endpoints that return only the required subset.

Example menu request:

```http
GET /institutions/uga/venues/bolton/menu?date=2026-07-18&meal_period=lunch
```

The backend:

1. finds the requested venue
2. finds its stations
3. finds offerings for the selected date and meal period
4. joins only the menu items referenced by those offerings
5. includes only the nutrition and tag fields needed by the client
6. calculates or includes effective availability
7. returns a compact JSON snapshot

---

# 34. Example Menu Snapshot

```json
{
  "institution": {
    "id": "uga",
    "name": "University of Georgia"
  },
  "venue": {
    "id": "bolton",
    "name": "Bolton Dining Commons"
  },
  "service_date": "2026-07-18",
  "meal_period": "lunch",
  "generated_at": "2026-07-18T11:45:00-04:00",
  "stations": [
    {
      "id": "grill",
      "name": "Grill",
      "offerings": [
        {
          "id": "offering_123",
          "menu_item_id": "item_42",
          "menu_item": {
            "name": "Grilled Chicken Breast",
            "serving_size": "1 breast",
            "nutrition": {
              "calories": 240,
              "protein_g": 36,
              "carbohydrates_g": 2,
              "fat_g": 8
            },
            "dietary_tags": [
              "gluten_free"
            ],
            "allergens": []
          },
          "availability": {
            "state": "likely_available",
            "negative_report_count": 1,
            "positive_report_count": 0,
            "confidence": 0.86
          }
        }
      ]
    }
  ]
}
```

The device receives only the current menu subset, not the complete catalog.

---

# 35. Catalog Search Endpoint

When a user wants to report a replacement or search for a food not on the current menu:

```http
GET /institutions/uga/menu-items/search?q=grilled+chicken
```

The backend searches the institution's menu-item catalog and returns a small result set.

Example response:

```json
{
  "query": "grilled chicken",
  "results": [
    {
      "id": "item_42",
      "name": "Grilled Chicken Breast"
    },
    {
      "id": "item_91",
      "name": "Herb Grilled Chicken"
    }
  ]
}
```

The app still does not download the full catalog.

---

# 36. Recommended MVP API Surface

```text
GET /institutions

GET /institutions/{institution_id}

GET /institutions/{institution_id}/venues

GET /venues/{venue_id}

GET /venues/{venue_id}/menu
    ?date=
    &meal_period=

GET /institutions/{institution_id}/menu-items/search
    ?q=

GET /menu-items/{menu_item_id}

POST /offerings/{offering_id}/reports

PATCH /offerings/{offering_id}/reports/{report_id}

POST /stations/{station_id}/reported-offerings

POST /institutions/{institution_id}/menu-item-suggestions
```

Admin or importer endpoints should remain separate from public user endpoints.

---

# 37. On-Device Recommendation Model

The PlateWise recommendation algorithm may run on the user's device.

The device should receive:

- selected venue
- selected meal period
- current offerings
- referenced menu-item nutrition
- referenced dietary tags
- referenced allergens
- effective availability state
- compact report summary

It should not receive:

- all historical menus
- all institutions
- the complete catalog
- raw user reports
- reporter identities
- import logs
- full raw source payloads

The device ranks the downloaded offerings using the user's local goals and preferences.

This supports:

- faster recommendations
- reduced server computation
- better privacy
- fewer repeated backend requests
- offline or degraded connectivity behavior

---

# 38. Device Cache

The client may cache only recent, relevant snapshots.

Example:

```text
University of Georgia
└── Bolton
    ├── today / lunch
    ├── today / dinner
    └── tomorrow / breakfast
```

Each snapshot should include:

```text
generated_at
source_snapshot_at
expires_at
schema_version
```

The app can request a refresh when the snapshot expires or when the backend indicates that the menu changed.

---

# 39. Change-Aware API Responses

To reduce unnecessary downloads, the API may support:

- `ETag`
- `If-None-Match`
- `Last-Modified`
- `If-Modified-Since`
- snapshot version IDs
- response content hashes

Example:

```http
GET /venues/bolton/menu?date=2026-07-18&meal_period=lunch
If-None-Match: "menu-snapshot-abc123"
```

If nothing changed:

```http
304 Not Modified
```

This is more efficient than making every device repeatedly download the same menu.

---

# 40. Recommended Constraints

## Institutions

```text
UNIQUE(slug)
```

## Venues

```text
UNIQUE(institution_id, slug)
```

## Stations

```text
UNIQUE(venue_id, slug)
```

## Menu items

When external IDs exist:

```text
UNIQUE(institution_id, external_id)
```

A normalized-name uniqueness constraint should not be blindly enforced because two legitimately different items may have similar names.

## Offerings

A likely starting constraint:

```text
UNIQUE(
    station_id,
    menu_item_id,
    service_date,
    meal_period,
    starts_at
)
```

This may need adjustment based on actual source data.

## Reports

Prevent duplicate active reports through application logic or a partial unique index tied to the active reporting window.

---

# 41. Recommended Indexes

```text
menu_items(institution_id, normalized_name)

menu_item_aliases(menu_item_id)
menu_item_aliases(normalized_alias)

venues(institution_id)
stations(venue_id)

menu_offerings(station_id, service_date, meal_period)
menu_offerings(menu_item_id, service_date)

nutrition_facts(menu_item_id, valid_from, valid_until)

offering_reports(offering_id, reported_at)
offering_reports(reporter_id, offering_id)

ingredients(institution_id, normalized_name)

data_imports(institution_id, started_at)
```

Full-text or trigram indexes may be added later for catalog search.

---

# 42. Record Deletion Policy

## Menu items

Do not automatically delete.

Use archival only for duplicates, invalid data, or manual cleanup.

## Ingredients

Do not automatically delete if they are still referenced historically.

## Venues and stations

Prefer `is_active = false` over deletion.

## Offerings

Offerings may expire naturally by date.

Historical offerings may be retained for analytics or removed later under a documented retention policy.

## Reports

Retain according to moderation, privacy, and analytics policy.

Live availability calculations should ignore expired reports even if the historical records remain stored.

---

# 43. Security and Abuse Prevention

Community reports create abuse risks.

The MVP should include:

- one active report per user/device per offering category
- server-side rate limits
- report timestamps generated or validated by the server
- reporter reputation only as a future enhancement
- moderation status
- report retraction
- device or account ban capability
- no public exposure of reporter identity
- suspicious-report logging
- threshold configuration per institution or venue

One malicious user must not be able to remove a dish from recommendations.

---

# 44. Privacy

The recommendation algorithm can run locally on the user's device.

The server does not need to store:

- calorie goals
- protein goals
- dietary objectives
- ranking weights
- personal meal selections

unless the user explicitly enables an account-based feature later.

For anonymous reports, PlateWise may use a privacy-preserving installation identifier rather than personal identity.

---

# 45. MVP Scope

The first database milestone should implement:

```text
institutions
venues
stations
menu_items
menu_item_aliases
nutrition_facts
ingredients
menu_item_ingredients
allergens
menu_item_allergens
dietary_tags
menu_item_dietary_tags
menu_offerings
offering_reports
data_imports
```

Optional for the earliest proof of concept:

```text
menu_item_suggestions
nutrition version history
staff verification
reporter reputation
complex recipe versioning
historical analytics warehouse
```

---

# 46. Immediate Implementation Order

## Step 1: Define the canonical data contract

Document:

- required menu-item fields
- optional nutrition fields
- ingredient representation
- allergen representation
- venue and station representation
- offering date/time representation
- source provenance
- unknown values
- estimated values

## Step 2: Create SQLAlchemy models

Implement the core tables and relationships.

## Step 3: Generate Alembic migration

Create the initial normalized schema.

## Step 4: Build fixture import

Create realistic UGA-style fixture data and import it through the same service layer future official imports will use.

## Step 5: Build targeted menu endpoint

Return one venue, date, and meal period with only referenced catalog data.

## Step 6: Build catalog search

Allow users to search institution-owned menu items for replacements and reports.

## Step 7: Build report storage

Store reports independently without changing official offering data.

## Step 8: Build availability aggregation

Start with configurable MVP thresholds and time decay.

## Step 9: Build on-device ranking

Use downloaded menu snapshots for local recommendations.

## Step 10: Add change-aware caching

Use snapshot hashes or ETags to avoid unnecessary downloads.

---

# 47. MVP Success Criteria

The database and API architecture is ready when PlateWise can:

1. Store an institution.
2. Store its venues and stations.
3. Store a separate institution-owned menu-item catalog.
4. Store nutrition and dietary data without duplicating it inside offerings.
5. Store offerings that point to catalog items.
6. retrieve one venue's menu for one date and meal period.
7. return only the menu items referenced by those offerings.
8. search the institution's catalog without downloading it entirely.
9. store multiple independent user reports.
10. prevent one report from controlling recommendation output.
11. calculate a temporary effective availability state.
12. preserve old menu items when they disappear from current menus.
13. detect source changes through timestamps and content hashes.
14. avoid exposing reporter identities to clients.
15. provide a compact snapshot suitable for on-device recommendation.

---

# 48. Final Recommended Architecture

```text
One PostgreSQL Database
│
├── Institution-Owned Catalog
│   ├── Menu Items
│   ├── Aliases
│   ├── Nutrition
│   ├── Ingredients
│   ├── Allergens
│   └── Dietary Tags
│
├── Institution Service Hierarchy
│   ├── Institutions
│   ├── Venues
│   └── Stations
│
├── Menus
│   └── Offerings
│       ├── station_id
│       └── menu_item_id → Catalog
│
├── Community Evidence
│   ├── Offering Reports
│   └── Menu Item Suggestions
│
└── Ingestion and Change Tracking
    └── Data Imports
```

The backend joins only the relevant records and sends compact JSON snapshots to each user's device.

The device receives only what it needs for the current venue, date, and meal period.

The recommendation algorithm can then run locally without downloading the full PlateWise catalog or database.

---

# 49. Final Summary

PlateWise should use one PostgreSQL database with separate normalized tables.

The institution owns two major branches:

```text
Institution
├── Menu Item Catalog
└── Venue and Station Hierarchy
```

The venue hierarchy contains offerings, and every offering points to an item in the separate catalog.

Menu items persist even when they are absent, sold out, replaced, or no longer scheduled.

User reports provide temporary evidence about a specific offering, but one report never controls recommendations.

The app never downloads the entire database. It receives targeted API responses containing only the current menu offerings and the catalog information referenced by those offerings.

This structure is appropriate for the PlateWise MVP while remaining flexible enough to support additional universities, hospitals, corporate campuses, and other institutional dining environments later.
