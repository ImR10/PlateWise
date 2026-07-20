# Recommendation Foundation — Phase 1 Audit

Milestone: **Recommendation Foundation** (`mvp/recommendation-foundation`).
Prepared before any implementation code. Facts below are confirmed by reading
the repository directly; each section separates **facts confirmed from code**,
**safe implementation choices**, and **true product decisions**.

Prior milestones: Database Foundation and Data Import Foundation are complete
(see `logs/MVP/database/LOG.md`, `logs/MVP/data-import/LOG.md`). The Targeted
Read API is being built separately; this milestone must not depend on it.

---

## 1. Confirmed relevant model concepts (facts from code)

- **Catalog vs offering split** (`db/src/platewise_db/models/catalog.py`,
  `db/src/platewise_db/models/menu.py`): `MenuItem` is the persistent food record;
  `MenuOffering` places it at a station/date/meal period with an
  `official_status` (`OfferingStatus`).
- **Nutrition** (`NutritionFacts`): versioned; source-provided and
  recipe-calculated records coexist (one active row per
  `(menu_item_id, provenance)`); nutrient columns are nullable `Numeric(10, 2)`
  mapped to `Decimal`; a missing nutrient is `NULL`, never zero.
- **Display precedence** (`MenuItem.display_nutrition()`): active
  source-provided nutrition is preferred; active **complete** recipe-calculated
  nutrition is the fallback; incomplete calculated nutrition is never
  authoritative. The recommendation engine must not invent a competing policy.
- **Allergens**: `MenuItemAllergen` carries `AllergenDeclarationType`
  (`contains` / `may_contain` / `facility_warning` / `unknown`) and a
  `ProvenanceSourceType`. Model docstrings state explicitly that absence of a
  declaration must never be treated as "allergen free".
- **Dietary tags**: `MenuItemDietaryTag` carries `ProvenanceSourceType` and an
  optional `confidence` (`Numeric(3, 2)`, 0–1). Tag names are normalized
  strings (`vegan`, `halal`, `gluten_free`, ...) — there is no dietary-tag
  enum; the catalog is open-ended by design.
- **Serving size**: `Decimal` size + free-text unit (`String(50)`), on both
  `MenuItem` (default) and `NutritionFacts` (per record); both nullable.
- **Availability**: `OfferingStatus` = `scheduled` / `available` /
  `unavailable` / `cancelled` / `unknown`. Community reports never overwrite
  official status; effective availability aggregation is a later milestone.

## 2. Reusable existing types and enums (facts from code)

Pure, ORM-free, source-neutral modules that this milestone can import without
touching FastAPI, the database, or the Read API:

- `db/src/platewise_db/enums.py` — `StrEnum`s: `AllergenDeclarationType`,
  `NutritionProvenance`, `NutritionReviewStatus`, `CalculationStatus`,
  `OfferingStatus`, `ProvenanceSourceType`. (The module imports SQLAlchemy's
  `Enum` type only for column helpers; using the enums requires no DB.)
- `api/src/platewise_api/imports/contracts.py` — Pydantic v2 conventions: frozen `_Contract`
  base (`extra="forbid", frozen=True`), bounded `Annotated` Decimal types
  (`NutrientDecimal`, `ServingDecimal`) with `allow_inf_nan=False` and
  SQL-compatible maxima, and `NutrientValues` (the 9 tracked nutrients, all
  optional, never coerced to zero).
- `db/src/platewise_db/constants.py` — `NUTRIENT_FIELDS` (stable 9-nutrient ordering).
- `db/src/platewise_db/decimal_utils.py` — `ROUND_HALF_UP` policy, `to_decimal`,
  `quantize_nutrient` (2 dp).
- `db/src/platewise_db/normalizers.py` — `normalize_name` (lowercase, whitespace
  collapse) used for all normalized-name matching.

## 3. Nutrition/provenance behavior that must be preserved (facts from code)

- Missing nutrients are `None`, never zero (contracts, models, importer docs).
- `NutritionProvenance` distinguishes `source_provided`, `recipe_calculated`,
  `manually_entered`, `estimated`; completeness is a separate `is_complete`
  flag plus `CalculationStatus` for calculated rows; `NutritionReviewStatus`
  flags records needing human review.
- Incomplete calculated nutrition is preserved but never authoritative.
- All nutrition arithmetic is `Decimal` with `ROUND_HALF_UP`; rounding only at
  output boundaries (`quantize_*` helpers); equality tested on quantized
  Decimals, never floats.

## 4. Allergen and dietary-tag semantics (facts from code)

- Allergen declarations are positive assertions with typed strength; there is
  no "allergen-free" assertion and no per-item "allergen data complete" flag
  in the schema. Unknown ≠ safe.
- Dietary tags are open-ended normalized names with provenance + optional
  confidence; there is no "tag data complete" flag. Absence of a tag does not
  prove the negative.
- `docs/mvp-sequence.md` records the MVP product stance: "unknown-allergen
  items are excluded from recommendations (browsable, but never treated as
  safe)".

## 5. Current uncertainty/completeness semantics (facts from code)

- Uncertainty is represented explicitly everywhere: nullable nutrients,
  `is_complete`, `CalculationStatus.partial`, `NutritionReviewStatus`,
  `AllergenDeclarationType.unknown`, `OfferingStatus.unknown`, dietary-tag
  `confidence`.
- The importer records structured warnings rather than silently discarding or
  zero-filling; `completed_with_errors` covers partial outcomes.

## 6. Proposed standalone domain contracts (safe implementation choices)

New package `api/src/platewise_api/recommendations/` (mirrors `api/src/platewise_api/imports/` structure), pure
domain, no FastAPI/ORM/Read-API imports. Contracts follow the `_Contract`
convention (Pydantic v2, frozen, `extra="forbid"`), all numerics `Decimal`.

- `RecommendationNutrition` — serving size/unit, `NutrientValues` (reused),
  `provenance: NutritionProvenance | None`, `is_complete`,
  `review_status`, `calculation_status`.
- `AllergenInfo` — normalized name + `AllergenDeclarationType`.
- `DietaryTagInfo` — normalized name + `ProvenanceSourceType` + optional
  confidence (0–1).
- `RecommendationItem` — stable string `item_id`, name, description,
  nutrition (optional), allergens + `allergen_data_complete: bool = False`,
  dietary tags + `dietary_tag_data_complete: bool = False`,
  `availability: OfferingStatus = UNKNOWN`, optional station/venue context.
  The safe default is *incomplete* safety metadata: an adapter must opt in to
  claiming completeness.
- `UserPreferences` — `GoalType` enum (`high_protein`, `lower_calorie`,
  `balanced`, `high_fiber`, `lower_sodium`, `vegetarian`), optional calorie
  target and/or min–max range (validated `min <= max`), optional protein
  target, excluded allergens, required/excluded dietary tags (normalized),
  disliked item ids/names, bounded `max_results`, and
  `SafetyMode` (`strict` / `permissive`, default **strict**).
- Result contracts — `ScoredRecommendation` (rank, total score, confidence,
  component scores, reason codes, cautions, human-readable explanations),
  `ExcludedItem` (machine-readable `ExclusionReason`s + explanations),
  `PlateSuggestion` (optional), `InputSummary` (counts + goal + mode only; no
  payload echo), `RecommendationResult` (ranked list, exclusions, warnings,
  summary, scoring policy version).

## 7. Proposed filtering rules (safe implementation choices)

Hard filters run before scoring; every exclusion carries ≥1 machine-readable
reason; nothing is silently dropped. Reasons (new `StrEnum`, uppercase values
to match the prompt's examples; no equivalent enum exists in the repo):

- `USER_EXCLUDED` — item id in disliked ids, or normalized name in disliked
  names.
- `UNAVAILABLE` — `OfferingStatus` is `unavailable` or `cancelled`
  (confirmed only; `unknown` is uncertainty, not exclusion).
- `ALLERGEN_CONFLICT` — an excluded allergen is declared `contains` (both
  modes) or `may_contain` / `facility_warning` (strict mode; permissive mode
  keeps the item with a caution).
- `UNKNOWN_ALLERGEN_STATUS` — strict mode + user excludes allergens + the
  item's allergen data is not complete (or the relevant declaration is
  `unknown`). Mirrors the documented MVP stance (§4).
- `DIETARY_CONFLICT` — a required tag is absent while tag data is complete,
  or an excluded tag is present. Goal `vegetarian` implies required tag
  `vegetarian` (explicitly satisfied by `vegetarian` or `vegan` via a
  documented constant — not keyword matching).
- `UNKNOWN_DIETARY_STATUS` — strict mode + required tags + tag data not
  complete and the tag absent.
- `INSUFFICIENT_NUTRITION_DATA` — no nutrition record or all nutrients
  `None`; in strict mode additionally: calories missing, or calculated
  nutrition with `is_complete=False` (permissive mode keeps these with a
  warning + confidence penalty).

## 8. Proposed scoring architecture (safe implementation choices)

- Pure function per component, each returning `Decimal` in [0, 1] or `None`
  (not computable — never treated as zero): protein adequacy, protein
  density (protein calories / total calories), calorie-target fit, calorie
  moderation, fiber adequacy, sodium moderation, data confidence.
- Central per-goal weight table (`GoalType -> {component: Decimal}`), each
  goal's weights summing to exactly 1; asserted by tests. All reference
  values (protein reference grams, sodium reference mg, ...) are named
  module-level constants with docstrings — no scattered magic numbers.
- Total score = `100 × Σ(wᵢ·cᵢ) / Σ(wᵢ)` over **available** components
  (renormalization keeps missing data from acting as zero), quantized to
  2 dp, so the scale is a bounded 0–100.
- Confidence ∈ [0, 1] from nutrition provenance/completeness/review status,
  missing-nutrient fraction, serving-size presence, and availability
  certainty; reported separately and used as tie-breaker #2.
- `SCORING_POLICY_VERSION` constant included in results.
- No ML, embeddings, LLM calls, or hidden heuristics.

## 9. Proposed deterministic tie-breaking (safe implementation choice)

Stable sort key: (1) total score desc, (2) confidence desc, (3) normalized
name asc, (4) item id asc. Pure functions, explicit sorts, no set/dict
iteration order dependence; repeated identical input ⇒ identical output.

## 10. Test strategy (follows repo conventions)

Pure unit tests, no DB/network (like `tests/test_import_units.py` /
`test_import_classification.py`); shared fixture-builder module
(`tests/recommendation_fixtures.py`, mirroring `tests/import_fixtures.py`);
Decimal equality on quantized values. Coverage per prompt: contract
validation (NaN/Inf/negatives/ranges/limits/duplicates/immutability), hard
filtering (all reasons, strict vs permissive, no silent exclusions), scoring
(goal-sensitivity, penalties, missing≠zero, bounded weights), ranking
(determinism, tie-breaks, limits, empty/one/all-tied), explanations
(machine-readable codes, stability, consistency with components), plus suite
regression: app import, `configure_mappers()`, OpenAPI generation.

## 11. Proposed file layout (matches prompt sketch + repo convention)

```text
api/src/platewise_api/recommendations/__init__.py
api/src/platewise_api/recommendations/contracts.py     # item/preference/result contracts
api/src/platewise_api/recommendations/enums.py         # GoalType, SafetyMode, reason/warning codes
api/src/platewise_api/recommendations/exceptions.py    # RecommendationError, DuplicateItemIdError
api/src/platewise_api/recommendations/filters.py       # hard eligibility filtering
api/src/platewise_api/recommendations/scoring.py       # weights, references, components, confidence
api/src/platewise_api/recommendations/explanations.py  # stable human-readable text
api/src/platewise_api/recommendations/plates.py        # basic deterministic plate assembly
api/src/platewise_api/recommendations/service.py       # orchestration + logging
api/tests/recommendation_fixtures.py
api/tests/test_recommendation_contracts.py
api/tests/test_recommendation_filters.py
api/tests/test_recommendation_scoring.py
api/tests/test_recommendation_ranking.py
api/tests/test_recommendation_explanations.py
api/tests/test_recommendation_service.py
docs/recommendation-foundation-architecture.md
logs/MVP/recommendation-foundation/LOG.md
```

`enums.py`, `exceptions.py`, and a fixtures module are additions to the
prompt's sketch, mirroring the existing `api/src/platewise_api/imports/` package shape.

## 12. Unresolved product decisions (owner input welcome; safe defaults chosen)

None block implementation. Defaults chosen (documented, easily revisited):

1. **Default safety mode** — strict (matches `docs/mvp-sequence.md`).
2. **`may_contain` / `facility_warning` in permissive mode** — kept eligible
   with a prominent caution (strict mode excludes). A stricter product rule
   can later exclude these everywhere.
3. **Dietary-tag trust** — tag presence satisfies a requirement in both
   modes; non-verified provenance (`imported`/`user_suggested`) adds a
   caution rather than excluding. True trust thresholds are a product call.
4. **Scoring references/weights** — reasonable documented constants
   (e.g. 30 g protein reference, 0–100 scale); product may retune later; the
   policy version string tracks any change.
5. **Plate assembly** — a deliberately small deterministic greedy assembler is
   included behind an opt-in preference flag (`assemble_plate=False` default);
   anything smarter (combinatorial optimization, 2–3 alternative plates,
   portion caps) is deferred to the recommendation API milestone.

## 13. Implementation plan

1. Contracts + enums + exceptions (validation-first, frozen, Decimal).
2. Hard filters returning machine-readable exclusion reasons.
3. Scoring: components, per-goal weights, confidence, policy version.
4. Explanations: stable strings from codes + component values.
5. Service orchestration (filter → score → rank → limit → result) with a
   single structured completion log event (counts/goal/duration only — no
   payloads or full preference details).
6. Optional plate assembly (greedy, bounded, deterministic, opt-in).
7. Comprehensive unit tests (no DB, no network).
8. `docs/recommendation-foundation-architecture.md` + milestone LOG.
9. Validation: `pytest`, `ruff check app alembic tests`, `alembic check`,
   app-import/mapper/OpenAPI smoke, `docker compose config --quiet`.
   No migration is expected (no schema change).
