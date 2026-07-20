# PlateWise MVP Data Import Foundation Plan

## Purpose

The PlateWise MVP must be able to collect usable menu and nutrition data even when institutions provide that data in different forms.

The importer must support two primary source shapes:

1. **Nutrition-ready menu items**  
   The source already provides serving information and nutrient values.

2. **Recipe-based menu items**  
   The source provides a recipe, ingredients, quantities, units, and yield, and PlateWise must calculate nutrition from those inputs.

The recipe-to-nutrition calculator is therefore an integral part of the MVP data collection system, not a later enhancement.

---

## Core MVP Principle

Both source paths must converge into the same normalized PlateWise data model:

```text
External source data
        ↓
Source adapter
        ↓
Raw payload preservation
        ↓
Record classification
        ├── nutrition-ready
        ├── recipe-ready
        ├── incomplete
        └── invalid
        ↓
Normalization
        ├── provided nutrition normalization
        └── recipe parsing and nutrition calculation
        ↓
Canonical PlateWise records
        ↓
Idempotent database persistence
```

The database and persistence layer should not depend on any one dining provider or source format.

---

## Supported MVP Input Paths

### Path A: Source-Provided Nutrition

Example source data:

```text
Grilled Chicken Breast
Serving size: 1 breast
Calories: 240
Protein: 36 g
Carbohydrates: 2 g
Fat: 9 g
Sodium: 420 mg
```

PlateWise should:

1. Validate the record.
2. Normalize nutrient names and units.
3. Preserve the original serving basis.
4. Store the source-provided nutrient values.
5. Record provenance showing that the nutrition came directly from the source.

Missing nutrient values must remain unknown or `NULL`. PlateWise must not convert missing values into zero.

---

### Path B: Recipe-Based Nutrition

Example source data:

```text
Grilled Chicken Breast

Ingredients:
- 6 oz chicken breast
- 1 tbsp olive oil
- 1 tsp salt

Yield:
- 2 servings
```

PlateWise should:

1. Parse each ingredient line.
2. Extract quantity, unit, ingredient name, and preparation details.
3. Normalize quantities and units.
4. Resolve each ingredient against a canonical ingredient nutrition source.
5. Convert ingredient quantities into edible grams.
6. Calculate each ingredient's nutrient contribution.
7. Sum the full recipe nutrient totals.
8. Divide totals by the recipe yield.
9. Store the resulting per-serving nutrition.
10. Record full calculation provenance and any unresolved issues.

---

## Nutrition Calculation Model

Once an ingredient has a known mass and reference nutrient profile:

```text
ingredient nutrient contribution
    = nutrient per 100 g × ingredient grams / 100
```

For a full recipe:

```text
recipe nutrient total
    = sum of all ingredient nutrient contributions
```

For per-serving values:

```text
per-serving nutrition
    = recipe nutrient total / number of servings
```

The arithmetic is simple. The difficult and important work is:

- ingredient identity resolution
- unit conversion
- portion-weight conversion
- raw versus cooked food distinction
- recipe yield interpretation
- ambiguous ingredient handling
- incomplete quantity handling

---

## Ingredient Nutrition Provider Boundary

The recipe calculator requires a separate nutrition reference source.

The source providing dining menus and recipes is not necessarily the same source providing nutrient composition for ingredients.

The architecture should define a provider boundary such as:

```python
class IngredientNutritionProvider:
    async def search_food(self, query: str): ...
    async def get_food(self, external_food_id: str): ...
    async def get_nutrients(self, external_food_id: str, grams: float): ...
```

The MVP may implement one provider, but the import system must not hard-code provider-specific data throughout the application.

---

## Internal Import Contracts

The importer should convert source-specific records into source-neutral internal contracts before persistence.

Conceptual contracts may include:

```text
ImportedInstitution
ImportedVenue
ImportedStation
ImportedMenuItem
ImportedServing
ImportedNutrition
ImportedRecipe
ImportedRecipeIngredient
ImportedOffering
ImportedAllergen
ImportedImportRun
```

A menu item may contain:

- source identifier
- name
- description
- serving basis
- source-provided nutrition
- recipe
- allergens
- source metadata
- provenance
- resolution status

Source-specific JSON, CSV, XML, or scraped structures must not leak into repository or persistence logic.

---

## Record Classification

Each incoming menu item should be classified before persistence.

### `nutrition_ready`

The source provides usable nutrient values and a serving basis.

### `recipe_ready`

The source provides a recipe with enough ingredient, quantity, unit, and yield information to attempt calculation.

### `incomplete`

The source provides partial data, such as:

- ingredients without quantities
- nutrition values without a serving basis
- recipe without yield
- unresolved ingredient units

The record should be preserved and flagged for review. PlateWise must not invent missing values.

### `invalid`

The source record is malformed or unusable.

The importer should log the failure and skip the record.

---

## Ingredient Resolution

Each recipe ingredient should preserve both the original source text and PlateWise's interpretation.

Example:

```text
Original:
"2 cups diced tomatoes"

Parsed:
quantity = 2
unit = cup
ingredient = tomato
preparation = diced
```

Each ingredient resolution should retain:

- original ingredient text
- parsed quantity
- parsed unit
- normalized ingredient name
- preparation notes
- selected canonical food identifier
- selected nutrition-provider identifier
- quantity converted to grams
- match method
- resolution status
- confidence or review status
- error details when unresolved

Suggested statuses:

```text
resolved
needs_review
unsupported_quantity
nutrition_match_missing
yield_missing
excluded_non_nutritive
invalid
```

Examples:

```text
"2 cups cooked white rice"
→ potentially resolved automatically
```

```text
"1 medium onion"
→ resolved only when a trustworthy portion weight is available
```

```text
"oil for frying"
→ needs review because absorbed quantity is unknown
```

```text
"salt to taste"
→ unresolved unless an amount is supplied
```

Unknown amounts must never silently become zero.

---

## Nutrition Provenance

PlateWise must distinguish how nutrition values were obtained.

Suggested provenance types:

```text
source_provided
recipe_calculated
manually_entered
estimated
```

A source-provided nutrition record should retain:

- source name
- source record identifier
- original serving basis
- original values
- import timestamp
- raw payload reference

A recipe-calculated record should retain:

- recipe version
- ingredient resolutions used
- nutrition provider and food identifiers
- unit conversions
- calculation timestamp
- recipe yield
- completeness status
- review status

These nutrition types must not be treated as equally authoritative.

When both source-provided and recipe-calculated nutrition are available, both should be preserved.

For MVP display behavior, source-provided nutrition should generally take precedence because it may reflect:

- institution-specific preparation
- branded ingredients
- cooking yield
- moisture changes
- absorbed oil
- actual production methods

Large discrepancies between provided and calculated values should be flagged for review.

---

## Import Outcomes

The importer needs more than a simple success/failure status.

Suggested outcomes:

### `complete_source_nutrition`

The source provided complete usable nutrition.

### `complete_calculated_nutrition`

The recipe was fully resolved and nutrition was calculated.

### `completed_with_errors`

The import succeeded overall, but some records or ingredients were skipped or require review.

### `partial`

The menu item or recipe was stored, but publishable nutrition could not be completed.

### `failed`

A source-level, structural, or transactional failure prevented the import.

A partial recipe may retain an internal nutrient subtotal, but incomplete nutrition must not be presented as authoritative to users.

---

## Idempotency and Identity

Running the same import repeatedly must not create duplicate institutions, venues, stations, menu items, recipes, ingredients, nutrition records, or offerings.

Source identifiers should be used whenever available.

Potential identity pattern:

```text
institution_id + source_system + source_record_id
```

Fallback name-based matching should be limited, explicit, institution-scoped, and logged because names are not guaranteed to be stable or unique.

The database audit must determine whether the current schema and unique constraints support this behavior.

---

## Import Run Tracking

Every import execution should record at least:

```text
source
institution
requested scope
started_at
completed_at
status
records fetched
records created
records updated
records skipped
records failed
ingredients resolved
ingredients unresolved
nutrition records provided
nutrition records calculated
error summary
raw payload reference
```

Raw source data should be preserved sufficiently for debugging and reproducibility.

For the MVP, this may be stored:

- directly in PostgreSQL as JSON, or
- as a referenced raw snapshot

The final choice should be based on the database audit and expected payload size.

---

## Transaction and Failure Behavior

Recommended MVP flow:

```text
fetch source data outside transaction
validate source response outside transaction
preserve raw payload
classify and normalize records

begin transaction
    upsert hierarchy
    upsert catalog entities
    persist recipes and ingredient resolutions
    persist nutrition
    persist offerings
    finalize import run
commit
```

A source-level failure should abort the import.

An individual malformed item may be skipped and logged when tolerant processing is enabled.

An empty or suspicious source response must never cause existing valid data to be erased automatically.

---

## Recommended Package Boundaries

Conceptual structure:

```text
api/src/platewise_api/
└── imports/
    ├── __init__.py
    ├── contracts.py
    ├── enums.py
    ├── exceptions.py
    ├── service.py
    ├── classifiers.py
    ├── provenance.py
    ├── sources/
    │   ├── __init__.py
    │   └── base.py
    ├── recipes/
    │   ├── parser.py
    │   ├── units.py
    │   ├── resolver.py
    │   └── calculator.py
    └── nutrition/
        ├── provider.py
        └── normalizer.py
```

The implemented repository boundary supersedes this original conceptual tree:
normalization/precision utilities and the persistence repository live in
`db/src/platewise_db/`, while orchestration and source adapters remain in
`api/src/platewise_api/imports/`.

Conceptual responsibilities:

### Source adapter

Fetches or reads source data and returns raw source records.

### Classifier

Determines whether a record is nutrition-ready, recipe-ready, incomplete, or invalid.

### Normalizer

Transforms source-specific fields into PlateWise internal contracts.

### Recipe parser

Extracts structured ingredient and yield data from supported recipe formats.

### Ingredient resolver

Maps normalized recipe ingredients to canonical foods in the nutrition provider.

### Unit converter

Converts supported quantities and portion units into grams.

### Nutrition calculator

Aggregates ingredient nutrients and calculates per-serving nutrition.

### Import service

Coordinates the complete import workflow.

### Repository layer

Performs idempotent persistence using the existing database model.

---

## MVP Scope

The `mvp/data-import-foundation` milestone should include:

1. A complete audit of the existing PlateWise database.
2. Source-neutral import contracts.
3. Raw payload preservation.
4. Record classification.
5. Source-provided nutrition normalization.
6. Structured recipe parsing.
7. Ingredient identity resolution through a provider interface.
8. Supported unit and portion conversion into grams.
9. Recipe nutrient aggregation.
10. Per-serving calculation using recipe yield.
11. Nutrition provenance.
12. Explicit incomplete and review states.
13. Idempotent database persistence.
14. Import run and error tracking.
15. Fixtures for both nutrition-label and recipe inputs.
16. Unit, integration, and migration tests.
17. Documentation and milestone logging.

---

## Explicitly Out of Scope for This Milestone

The MVP should not attempt to build:

- a universal importer for every possible provider
- multiple nutrition providers at implementation time
- arbitrary website scraping infrastructure
- distributed workers
- Redis
- Celery
- Kafka
- real-time ingestion
- automatic scheduling
- a full review dashboard
- LLM-only authoritative ingredient matching
- unsupported vague quantity estimation
- scientific cooking-loss modeling
- absorbed-oil estimation
- automatic interpretation of “to taste”
- complete historical backfills
- silent nutritional guessing

The system may preserve unresolved records for later review, but it must not invent authoritative nutrition values.

---

## Database Audit Required Before Implementation

Before writing the importer, Claude should audit the current database implementation and report:

1. The exact schema and relationships for:
   - institutions
   - venues
   - stations
   - menu items
   - servings
   - nutrition records
   - ingredients
   - allergens
   - recipes
   - recipe ingredients
   - offerings
   - import runs
   - provenance
   - review or error states

2. Existing unique constraints and whether they support idempotent imports.

3. Whether external source identifiers can be stored on all necessary entities.

4. Whether ingredient quantities, units, gram conversions, and preparation notes are representable.

5. Whether recipe yield and per-serving calculation metadata are representable.

6. Whether nutrition records distinguish:
   - source-provided
   - recipe-calculated
   - manual
   - estimated

7. Whether multiple nutrition versions can coexist without overwriting history.

8. Whether incomplete or unresolved recipes can be stored safely.

9. Whether ingredient-resolution decisions and provider identifiers can be preserved.

10. Whether import runs, raw payloads, errors, and record counts are supported.

11. Existing cascade, delete, and update behavior.

12. Existing fixture and test infrastructure.

13. Required schema changes and migrations before importer implementation.

Claude should perform this audit before modifying code and should not build around assumptions that conflict with the database foundation.

---

## MVP Success Criteria

The milestone is complete when PlateWise can reliably demonstrate both paths:

### Nutrition-label fixture

A source-provided menu item is imported, normalized, persisted, and re-imported without duplication.

### Recipe fixture

A structured recipe is parsed, all ingredients are resolved, quantities are converted to grams, nutrition is calculated, per-serving values are persisted, and re-importing does not create duplicates.

### Incomplete fixture

A recipe containing an unresolved ingredient or vague quantity is preserved and marked for review without fabricating complete nutrition.

### Provenance fixture

The database clearly distinguishes source-provided nutrition from recipe-calculated nutrition.

### Failure fixture

A malformed source record is logged and skipped without corrupting the broader import.

---

## Guiding Rule

> PlateWise should preserve source facts, calculate only from traceable inputs, expose uncertainty honestly, and never present invented values as authoritative nutrition.
