# Recommendation Foundation — Architecture

Milestone: **Recommendation Foundation** (`mvp/recommendation-foundation`).
Phase 1 audit: `docs/recommendation-foundation-audit.md`.

## Scope

A standalone, deterministic, testable recommendation engine in
`app/recommendations/`. It accepts normalized menu-item inputs and user
preference/goal inputs and produces eligible items, excluded items with
machine-readable reasons, ranked recommendations with transparent scoring,
uncertainty warnings, and (opt-in) a basic assembled plate.

Deliberately **not** in this milestone: API routes, database repositories, the
Targeted Read API (built separately), availability aggregation, community
reports, accounts, ML/LLM ranking, or multi-day planning. No schema change and
no migration. The engine will later be fed by a thin adapter that maps Read
API responses onto its contracts.

```text
Read API response ── adapter (later milestone) ──► RecommendationItem
                                                        │
                                              hard safety filters
                                                        │
                                               goal-based scoring
                                                        │
                                             deterministic ranking
                                                        │
                                              RecommendationResult
```

## Package layout

```text
app/recommendations/
  contracts.py     # frozen Pydantic v2 DTOs (input + result)
  enums.py         # goals, safety modes, reason/caution/warning codes
  exceptions.py    # RecommendationError, DuplicateItemIdError
  filters.py       # hard eligibility filtering (before any scoring)
  scoring.py       # weights, references, components, confidence, version
  explanations.py  # total code -> human text mappings
  plates.py        # optional greedy plate assembly
  service.py       # orchestration + structured completion logging
```

The engine reuses pure, ORM-free shared modules — `app.db.enums` (StrEnums),
`app.imports.contracts` (`NutrientValues`, bounded Decimal types),
`app.imports.decimal_utils` (ROUND_HALF_UP policy), and
`app.imports.normalizers.normalize_name` — rather than defining a second
nutrition or normalization policy. It imports nothing from FastAPI routes,
SQLAlchemy models, or Read API schemas.

## Contracts

All contracts are frozen (`frozen=True`), reject unknown fields
(`extra="forbid"`), use `Decimal` for numerics with bounds and
`allow_inf_nan=False` (NaN/Infinity/negative values are rejected), and
represent missing data as `None` — never zero.

- **`RecommendationItem`** — stable `item_id`, name, description, optional
  `RecommendationNutrition` (serving info, `NutrientValues`,
  `NutritionProvenance`, `is_complete`, review status), allergen declarations
  (`AllergenDeclarationType`), dietary tags (`ProvenanceSourceType` +
  optional confidence), `OfferingStatus` availability, optional station/venue
  display context. `allergen_data_complete` and `dietary_tag_data_complete`
  default to **False**: adapters must explicitly assert exhaustive safety
  metadata.
- **`UserPreferences`** — goal, safety mode, optional calorie target and/or
  min–max range (validated), optional protein target, excluded allergens,
  required/excluded dietary tags, disliked item ids/names, bounded
  `max_results` (1–50, default 10), `assemble_plate` flag. Name lists are
  normalized, deduplicated, and sorted at validation time.
- **`RecommendationResult`** — ranked `ScoredRecommendation`s, `ExcludedItem`s
  (each with ≥1 reason code + matching explanations), result-level warnings
  with explanations, an `InputSummary` (shape/counts only — no preference
  values echoed), `result_count`, `scoring_policy_version`, optional
  `PlateSuggestion`.

Duplicate input item ids raise `DuplicateItemIdError`.

## Supported goals

`high_protein`, `lower_calorie`, `balanced`, `high_fiber`, `lower_sodium`,
`vegetarian`. Goals are enum values — no keyword matching or free-form
interpretation. `vegetarian` implies a hard required-tag filter (satisfied by
a `vegetarian` **or** `vegan` tag via the explicit
`REQUIRED_TAG_SATISFIED_BY` table) and scores with the balanced weights.

## Hard filtering (before scoring)

Every exclusion carries one or more machine-readable codes; nothing is
silently discarded. `strict` mode (default) refuses to treat unknown safety
data as safe; `permissive` mode keeps such items with explicit cautions.

| Reason code | Trigger |
| --- | --- |
| `USER_EXCLUDED` | item id in disliked ids, or normalized name in disliked names |
| `UNAVAILABLE` | official status `unavailable` or `cancelled` (confirmed only; `unknown` is uncertainty, not exclusion) |
| `ALLERGEN_CONFLICT` | excluded allergen declared `contains` (both modes); `may_contain`/`facility_warning` also conflict in strict mode (caution in permissive) |
| `UNKNOWN_ALLERGEN_STATUS` | strict mode, user excludes allergens, and the item's allergen data is incomplete or declared `unknown` |
| `DIETARY_CONFLICT` | required tag absent while tag data is complete, or an excluded tag is present (both modes) |
| `UNKNOWN_DIETARY_STATUS` | strict mode, required tag absent, tag data incomplete |
| `INSUFFICIENT_NUTRITION_DATA` | no nutrition / all nutrients unknown; in strict mode also missing calories or `is_complete=False` nutrition |

## Scoring model

Documented fully in `app/recommendations/scoring.py`
(`SCORING_POLICY_VERSION = "1.0.0"`; any change to weights, references, or
formulas bumps it).

- **Scale**: total score is **0–100** (higher is better); each component is a
  `Decimal` in [0, 1]; confidence is a separate 0–1 value. Quantization:
  components 4 dp, totals/confidence 2 dp, `ROUND_HALF_UP`.
- **Components**: protein adequacy (vs. per-item share of the protein target,
  or a 30 g reference), protein density (fraction of calories from protein
  vs. a 30% reference), calorie fit (per-item share of the user's
  target/range, linear falloff outside), calorie moderation (lower calories
  score higher, 0 at 800 kcal), fiber adequacy (8 g reference), sodium
  moderation (0 at 1500 mg), data confidence.
- **Missing data**: a component whose inputs are unknown is *absent*, never
  zero. The total renormalizes over available weights:
  `total = 100 x sum(w_i * c_i) / sum(w_i)` over available components. An
  explicit zero nutrient is penalized; an unknown one is not.
- **Weights**: centralized per-goal in `GOAL_WEIGHTS`; every goal's weights
  sum to exactly 1 (validated at import time and by tests). Plate-level
  targets are converted to per-item targets by dividing by
  `PLATE_ITEM_COUNT = 3`.
- **Confidence**: product of factors — nutrition provenance (source-provided
  1.00, manually entered 0.95, recipe-calculated 0.85, estimated 0.70,
  unknown 0.50), incompleteness (×0.60), needs-review (×0.85), unknown
  serving (×0.90), availability (available 1.00, scheduled 0.95, unknown
  0.85), and the fraction of the six core nutrients known (floor 0.50).
- No ML, embeddings, LLM calls, or hidden heuristics.

## Deterministic ordering

Stable ranking key: (1) total score descending, (2) confidence descending,
(3) normalized name ascending, (4) item id ascending. Pure functions and
explicit sorts throughout; repeated identical input produces identical output
(asserted by tests).

## Uncertainty behavior

Uncertainty is always explicit, never hidden:

- strict mode **excludes** on unknown safety metadata the user depends on
  (with `UNKNOWN_*` reason codes, and a result-level warning explaining that
  exclusions were data gaps, not confirmed conflicts);
- permissive mode keeps items with **cautions**
  (`MAY_CONTAIN_EXCLUDED_ALLERGEN`, `ALLERGEN_DATA_INCOMPLETE`,
  `DIETARY_DATA_INCOMPLETE`, `NUTRITION_INCOMPLETE`, `MISSING_NUTRIENTS`,
  `SERVING_SIZE_UNKNOWN`, `AVAILABILITY_UNCERTAIN`, ...);
- calculated/estimated/incomplete nutrition, unknown serving sizes, and
  unconfirmed availability reduce the confidence value with documented
  factors;
- absent allergen data is never read as allergen-free, and absent nutrients
  are never read as zero.

## Explanation behavior

`explanations.py` maps every reason/caution/exclusion/warning code to a
stable human-readable sentence via total dictionaries (totality is
test-enforced, so a new code cannot ship without text). Text never claims
medical certainty or allergen safety; uncertainty wording is preserved.
Positive reasons are emitted only when the matching score component crosses a
documented threshold, so explanations always match actual score components.

## Plate assembly (basic, opt-in)

`preferences.assemble_plate=True` enables a single greedy, deterministic pass
over the ranked eligible items (hard constraints already applied): at most 4
distinct items; with a calorie budget (explicit range, or target ±10%) only
items with known calories are combined, the upper bound is never exceeded,
and selection stops at the lower bound; without a budget the plate is the top
3 ranked items plus an explicit warning. Nutrient totals sum one serving per
item and become `None` (with a warning) if any item's value is unknown.
Shortfalls against calorie/protein targets produce warnings. Anything more
(combinatorial optimization, multiple alternative plates, portion caps,
multi-day planning) is deferred.

## Observability

One stdlib structured log event per run (`recommendation_run_completed`) with
counts, goal, safety mode, plate flag, duration, and policy version. User
preference payloads, item payloads, and full results are never logged.

## Strict/permissive summary

| Situation | strict (default) | permissive |
| --- | --- | --- |
| Excluded allergen declared `contains` | exclude | exclude |
| Excluded allergen `may_contain`/`facility_warning` | exclude | keep + caution |
| Allergen data incomplete (user excludes allergens) | exclude | keep + caution |
| Required tag absent, tag data complete | exclude | exclude |
| Required tag absent, tag data incomplete | exclude | keep + caution |
| Excluded tag present | exclude | exclude |
| Calories unknown / nutrition incomplete | exclude | keep + caution/penalty |

## Known limitations

- Reference values (30 g protein, 800 kcal, 1500 mg sodium, 3 items/plate)
  are documented MVP defaults, not personalized guidance; the engine is a
  dining recommendation tool, not a medical device.
- Dietary-tag trust is binary presence plus provenance cautions; no
  confidence thresholds yet.
- Availability is the official source status only; community-report
  aggregation is a later milestone.
- Plate assembly is greedy (one plate, ranking order), not optimal, and skips
  calorie-unknown items when a budget exists.
- `station_name`/`venue_name` are display passthroughs; no scoring effect.

## Future Read API adapter boundary

When the Targeted Read API lands, add a thin adapter (suggested:
`app/recommendations/adapters.py` or inside the API layer) that maps read
models onto `RecommendationItem` — choosing nutrition via the existing
`display_nutrition()` precedence, mapping allergen declarations and dietary
tags with their provenance, and setting the `*_data_complete` flags only when
the source guarantees exhaustive metadata. The engine itself needs no change;
`POST /recommendations` then becomes: load items → adapt → `recommend()` →
serialize `RecommendationResult`.
