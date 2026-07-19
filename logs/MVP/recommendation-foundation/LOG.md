# MVP — Recommendation Foundation — LOG

Milestone: **Recommendation Foundation** (`mvp/recommendation-foundation`).
Append new entries at the bottom; do not rewrite history. Same tone/structure
as `logs/MVP/database/LOG.md` and `logs/MVP/data-import/LOG.md`.

Plan of record: `docs/PlateWise_Recommendation_Foundation_Claude_Prompt.md`.

---

## 2026-07-19 10:12 EDT — Phases 1–2: audit and implementation

### Phase / milestone

Phase 1 (audit) and Phase 2 (implementation + validation) in one pass. The
audit found no blocking product decision, destructive schema change, or
architectural redesign, so implementation proceeded per the plan of record.
No Git operation was run. No schema or migration change was made.

### Audit summary

Created `docs/recommendation-foundation-audit.md`. Confirmed from code: the
catalog/offering split; versioned coexisting nutrition with a provenance enum
and `display_nutrition()` precedence (source-provided, then *complete*
recipe-calculated); nullable `Decimal` nutrients (missing ≠ zero); allergen
declarations whose absence never means allergen-free; open-ended normalized
dietary tags with provenance + confidence; `OfferingStatus` availability; the
ROUND_HALF_UP Decimal policy; frozen Pydantic v2 contract conventions;
DB-free unit-test style; and stdlib structured event logging. The documented
MVP product stance (unknown-allergen items are excluded from recommendations)
was carried into the default strict safety mode. Five product-tunable
defaults (safety mode default, may-contain handling, tag trust, scoring
references, plate assembly scope) were recorded in audit §12 with safe
defaults — none blocked implementation.

### Implementation summary

New standalone domain package `app/recommendations/` (no FastAPI, database,
or Read API dependencies; reuses `app.db.enums`, `app.imports.contracts`
value types, `app.imports.decimal_utils`, and `normalize_name` rather than
inventing a second policy):

- **Contracts**: `RecommendationItem` (+ nutrition/allergen/tag sub-DTOs with
  provenance and completeness), `UserPreferences` (6 enum goals,
  strict/permissive safety mode, targets/ranges, exclusions, dislikes,
  bounded `max_results`), and result DTOs (`ScoredRecommendation`,
  `ExcludedItem`, `PlateSuggestion`, `InputSummary`,
  `RecommendationResult`). All frozen, `extra="forbid"`, Decimal-typed,
  NaN/Infinity/negatives rejected; safety-metadata completeness defaults to
  False.
- **Hard filters** (`filters.py`): 7 machine-readable exclusion reasons; no
  silent exclusions; strict mode never treats unknown safety data as safe;
  permissive mode converts unknowns into cautions. Vegetarian goal is a hard
  filter satisfied by `vegetarian` or `vegan` via an explicit lookup table.
- **Scoring** (`scoring.py`): policy version `1.0.0`; 7 bounded [0, 1]
  components; per-goal weight tables summing to exactly 1 (validated at
  import); named reference constants; renormalization over available
  components so missing values never act as zero; multiplicative confidence
  factors; positive-reason thresholds. Scale 0–100, `ROUND_HALF_UP`.
- **Explanations** (`explanations.py`): total code→text mappings for
  positives, cautions, exclusions, and warnings (totality test-enforced); no
  safety or medical certainty claims.
- **Ranking/service** (`service.py`): duplicate-id rejection; deterministic
  sort (score desc, confidence desc, normalized name asc, id asc); result
  limit; result-level warnings; one structured `recommendation_run_completed`
  log event (counts/goal/mode/duration/version only — no payloads).
- **Plate assembly** (`plates.py`, opt-in): single greedy deterministic pass;
  ≤4 items; calorie budget honored (target ±10% or explicit range);
  calorie-unknown items skipped under a budget; nutrient totals go `None`
  (never zero) when any item's value is unknown; shortfall warnings.

### Files created

- `apps/api/app/recommendations/{__init__,contracts,enums,exceptions,
  filters,scoring,explanations,plates,service}.py`
- `apps/api/tests/recommendation_fixtures.py`
- `apps/api/tests/test_recommendation_{contracts,filters,scoring,ranking,
  explanations,service}.py`
- `docs/recommendation-foundation-audit.md`
- `docs/recommendation-foundation-architecture.md`
- `logs/MVP/recommendation-foundation/LOG.md` (this log)

### Files modified

- None outside the new package/tests/docs. Importer, models, migrations,
  API routes, and existing tests are untouched.

### Schema / migration changes

- **None. No migration was created; the schema did not change.**
  `alembic check` confirms no drift.

### Important decisions

- Default safety mode is **strict**, matching `docs/mvp-sequence.md`
  ("unknown-allergen items are excluded from recommendations").
- `may_contain`/`facility_warning` conflict in strict mode; in permissive
  mode they stay eligible with a `MAY_CONTAIN_EXCLUDED_ALLERGEN` caution.
- Reason/caution/warning codes are UPPERCASE StrEnums (matching the plan's
  examples); goal/mode enums are lowercase like existing setting enums.
- Reused shared pure modules from `app.imports` (contracts value types,
  Decimal policy, normalizer) instead of duplicating them; noted in the audit
  that a shared `app/domain` home is a possible future refactor.
- Plate assembly shipped in its intentionally limited greedy form behind an
  opt-in flag (default off) rather than being deferred outright.

### Tests added

73 new DB-free unit tests (suite 120 → 193): contract validation
(NaN/Infinity, negatives, ranges, limits, duplicates, immutability,
normalization), all hard-filter behaviors in both safety modes, scoring
goal-sensitivity/penalties/confidence/missing≠zero/bounded-deterministic
weights, ranking determinism + tie-breaks + limits + empty/one/tied inputs,
explanation totality/stability/consistency, service summary/logging/plate
behaviors, and an app-import + OpenAPI + `configure_mappers()` smoke test.

### Exact validation commands and results

From `apps/api` (PostgreSQL started via `docker compose up -d db`; explicit
localhost URLs per the data-import milestone convention):

- `TEST_DATABASE_URL=postgresql+psycopg://platewise:platewise_dev_password@localhost:5432/platewise_test DATABASE_URL=postgresql+psycopg://platewise:platewise_dev_password@localhost:5432/platewise pytest`
  → **193 passed, 1 warning in 1.86s** (the warning is the pre-existing
  Starlette/httpx testclient deprecation).
- `ruff check app alembic tests` → **All checks passed!**
- `DATABASE_URL=postgresql+psycopg://platewise:platewise_dev_password@localhost:5432/platewise alembic check`
  → **No new upgrade operations detected.**
- `python -c "from app.main import app; from sqlalchemy.orm import configure_mappers; configure_mappers(); print(app.title)"`
  → **PlateWise API**.
- From repository root, `docker compose config --quiet` → valid (exit 0).

Note: without the localhost URLs, DB-backed tests skip (or, for the migration
roundtrip test, fail to resolve Compose host `db`) — same environment caveat
recorded in the data-import log.

### Deviations from the plan of record

- Added `enums.py`, `exceptions.py`, and `plates.py` beyond the plan's
  sketched file list, mirroring the existing `app/imports/` package shape
  (the plan allowed layout adaptation).
- No other deviations; all scope restrictions respected.

### Known limitations / follow-up

- Scoring references/weights are documented MVP defaults pending product
  tuning (policy version tracks changes).
- Dietary-tag trust uses presence + provenance cautions; no confidence
  thresholds yet.
- Plate assembly is single-plate greedy; the MVP's "2–3 plates" UX belongs to
  the recommendation API milestone.
- Availability reflects official status only; community-report aggregation is
  a later milestone.

### Recommended next work

After the Targeted Read API lands: a thin adapter mapping read models onto
`RecommendationItem` (nutrition via `display_nutrition()` precedence,
allergens/tags with provenance, `*_data_complete` flags set only when the
source guarantees exhaustive metadata), then `POST /recommendations` calling
`app.recommendations.recommend()` and serializing `RecommendationResult`.
