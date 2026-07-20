# PlateWise Data Import Foundation — Phase 3 Polish Audit

**Date:** 2026-07-18 19:31 EDT  
**Branch:** `mvp/data-import-foundation` (owner-supplied; no Git commands were run)  
**Plan of record:** `docs/mvp-data-import-plan.md`  
**Scope:** focused audit and hardening of the implemented synchronous importer

## Executive summary

The Phase 2 architecture remains appropriate for the MVP. The source and
nutrition-provider boundaries are separate, domain contracts do not expose ORM
models, nutrition provenance and display precedence are modeled correctly,
recipe history is preserved, per-record savepoints isolate tolerant failures,
and the test harness derives a dedicated `*_test` database rather than using the
development database.

The audit found no critical issue and no reason for a redesign, destructive
migration, major dependency, real provider, async work, or product decision.
It did find concrete validation, identity, observability, versioning, and
efficiency gaps. Findings marked **fix now** are addressed in this Phase 3 pass;
deferred findings are bounded follow-up work that does not invalidate the MVP
foundation.

Finding types below are explicit: **verified defect**, **maintainability
concern**, **optimization opportunity**, **documentation drift**, or **optional
recommendation**.

## Findings

### DIA-001 — Unbounded and non-finite numeric inputs

- **Area:** behavioral edge cases; security and data integrity
- **Severity:** high
- **Type:** verified defect
- **File / symbol:** `api/src/platewise_api/imports/contracts.py` — numeric DTO fields;
  `api/src/platewise_api/imports/nutrition/provider.py` — provider numeric DTO fields
- **Verified behavior:** Pydantic accepts negative nutrient values, negative
  ingredient quantities, zero/negative portion weights, `NaN`, `Infinity`, and
  values whose precision exceeds the target SQL `Numeric` columns. Negative
  recipe quantities can therefore produce authoritative negative nutrition;
  non-finite or oversized values fail late during calculation or database flush.
- **Why it matters:** expected bad input can produce false nutrition or an
  uncontrolled persistence exception instead of a typed record failure.
- **Proposed correction:** add finite, non-negative, storage-compatible Decimal
  bounds to contracts and provider DTOs; require positive provider reference and
  portion gram weights. Preserve zero nutrient values as valid.
- **Disposition:** **fix now**.
- **Required coverage:** negative nutrient/quantity, non-finite values, zero
  servings, and invalid provider weights.

### DIA-002 — Payload shape, size, depth, and collection counts are unbounded

- **Area:** security and data integrity; behavioral edge cases
- **Severity:** high
- **Type:** verified defect
- **File / symbol:** `api/src/platewise_api/imports/sources/fixture.py` —
  `FixtureDiningSource.fetch`; `api/src/platewise_api/imports/contracts.py` — DTOs
- **Verified behavior:** a non-list `menu_items` value is iterated as an arbitrary
  iterable, and raw payload depth/serialized size, record counts, recipe line
  counts, and source strings have no application limits.
- **Why it matters:** malformed top-level data is misclassified as many malformed
  records, while deeply nested or oversized fixture payloads can consume
  disproportionate memory/CPU and oversized strings can reach bounded database
  columns.
- **Proposed correction:** validate top-level collection shapes, enforce
  conservative MVP limits for payload bytes/depth/counts and strings, and return
  `SourceError` or per-record validation failures before domain writes.
- **Disposition:** **fix now**.
- **Required coverage:** malformed top level, excessive depth, excessive recipe
  lines, and boundary-sized valid data.

### DIA-003 — Conflicting and duplicate source identities are not isolated

- **Area:** security and data integrity; behavioral edge cases
- **Severity:** high
- **Type:** verified defect
- **File / symbol:** `api/src/platewise_api/imports/sources/fixture.py` —
  `FixtureDiningSource.fetch`; `api/src/platewise_api/imports/service.py` — `run_import`
- **Verified behavior:** hierarchy and item records may declare a
  `source_system` different from the payload institution, and duplicate
  `(source_system, external_id)` menu items in one payload are processed
  sequentially. Conflicting duplicates can silently turn one source record into
  multiple updates and misleading counters.
- **Why it matters:** a source adapter can accidentally or maliciously write
  identities outside its run namespace, and payload-local conflicts are hidden.
- **Proposed correction:** require one source-system namespace within a fixture
  run; reject conflicting hierarchy at the source boundary and convert duplicate
  or conflicting item identities into structured malformed-record failures.
- **Disposition:** **fix now**.
- **Required coverage:** nested source mismatch, identical duplicate identity,
  and conflicting duplicate identity.

### DIA-004 — Recipe source-text-only changes do not create a version

- **Area:** behavioral edge cases; data integrity
- **Severity:** medium
- **Type:** verified defect
- **File / symbol:** `db/src/platewise_db/repositories/imports.py` —
  `recipe_content_hash`
- **Verified behavior:** `ImportedRecipe.source_text` is persisted but omitted
  from the recipe content hash. A changed original recipe body with unchanged
  structured fields is treated as unchanged.
- **Why it matters:** the stored active recipe body and version history can drift
  from the latest source, weakening raw provenance and the documented versioning
  contract.
- **Proposed correction:** include `source_text` in the meaningful recipe hash.
- **Disposition:** **fix now**.
- **Required coverage:** source-text-only change and reversion to an older body.

### DIA-005 — Discrepancy detection is skipped when only source nutrition changes

- **Area:** behavioral edge cases; observability
- **Severity:** medium
- **Type:** verified defect
- **File / symbol:** `api/src/platewise_api/imports/service.py` — `_process_item`
- **Verified behavior:** source-versus-calculated calorie comparison runs only
  when a recipe version is newly created. If the recipe is unchanged and the
  source-provided calories change materially, no discrepancy warning is stored.
- **Why it matters:** the review signal depends on which side changed, even
  though provenance rules require comparison whenever both complete values are
  present.
- **Proposed correction:** compare against the active calculated record whether
  the recipe was created, changed, or unchanged.
- **Disposition:** **fix now**.
- **Required coverage:** unchanged recipe plus changed source nutrition; no
  warning at or below the threshold.

### DIA-006 — No operational logging for import lifecycle or failures

- **Area:** observability
- **Severity:** medium
- **Type:** verified defect
- **File / symbol:** `api/src/platewise_api/imports/service.py` — `run_import`,
  `_process_item`
- **Verified behavior:** the importer writes database error rows but emits no
  Python log records for run start/completion/failure, counters, stage, duration,
  rollback, or incomplete calculations.
- **Why it matters:** operators cannot understand a running or failed import
  without querying the database, and source-level failures leave no run row.
- **Proposed correction:** add standard-library structured logging with stable
  event names and `extra` fields; never log raw/provider payloads, full malformed
  records, or ingredient text.
- **Disposition:** **fix now**.
- **Required coverage:** lifecycle fields, incomplete calculation event, failure
  stage, and absence of raw sensitive values.

### DIA-007 — Repeated ingredient resolution performs duplicate provider calls

- **Area:** performance
- **Severity:** medium
- **Type:** optimization opportunity
- **File / symbol:** `api/src/platewise_api/imports/service.py` — `_process_item`;
  `api/src/platewise_api/imports/recipes/resolver.py` — `_resolve_food`
- **Verified behavior:** every ingredient line calls `get_food` or `search_food`
  independently, even for the same deterministic provider identity/query within
  one import run.
- **Why it matters:** a future synchronous network provider would multiply
  latency and quota usage; even the fake repeats normalization and lookup work.
- **Proposed correction:** use a small run-scoped caching provider wrapper keyed
  by lookup method/value. Do not add an external cache.
- **Disposition:** **fix now**.
- **Required coverage / evidence:** a counting provider should show one call per
  unique id/query before/after (for two identical lookups: 2 → 1).

### DIA-008 — Provider cache persistence is append-only and duplicates DB lookups

- **Area:** performance; data integrity
- **Severity:** medium
- **Type:** maintainability concern and optimization opportunity
- **File / symbol:** `db/src/platewise_db/repositories/imports.py` —
  `upsert_provider_food`, `_provider_food_pk`, `persist_recipe_ingredients`
- **Verified behavior:** each resolved line queries `provider_foods` during
  upsert and again to obtain its PK; an existing provider food is never refreshed
  when nutrients, portions, name, or metadata change.
- **Why it matters:** query count grows per line and persisted provider provenance
  may no longer match the provider data used for a calculation.
- **Proposed correction:** deduplicate food upserts per item/run and pass returned
  rows into ingredient persistence. Define a provider snapshot/version policy
  before mutating cached nutrient composition in place.
- **Disposition:** **partially fix now** (remove duplicate in-run queries);
  **defer** cache refresh/version policy because overwriting reference data would
  rewrite the historical meaning of old calculations.
- **Required coverage:** repeated food lines use one upsert/PK lookup; document
  the immutable-cache limitation.

### DIA-009 — Public result DTO exposes a private mutable counters type

- **Area:** API and internal ergonomics; code quality
- **Severity:** low
- **Type:** maintainability concern
- **File / symbol:** `api/src/platewise_api/imports/service.py` — `_Counters`, `ImportResult`
- **Verified behavior:** the public `ImportResult.counters` annotation is a
  private `_Counters` dataclass, `import_id` is typed as `object`, and callers can
  mutate the returned summary.
- **Why it matters:** the intended entry point is easy to use but its public
  return contract is underspecified and appears internal.
- **Proposed correction:** expose typed `ImportCounters`, type `import_id` as
  UUID, and keep aggregation mutation internal while returning a stable summary.
- **Disposition:** **fix now** without changing field names or status values.
- **Required coverage:** caller-visible types/fields and existing result behavior.

### DIA-010 — Unsafe exception text and raw ingredient context reach errors

- **Area:** security; observability
- **Severity:** medium
- **Type:** verified defect
- **File / symbol:** `api/src/platewise_api/imports/service.py` — exception handler and
  unresolved-ingredient error creation
- **Verified behavior:** arbitrary `str(exc)` is persisted as an import error and
  full source ingredient text is stored in `ingredient_context`; item names are
  used as fallback record references.
- **Why it matters:** driver/provider exceptions and source text may contain
  credentials, payload fragments, or sensitive values; bounded context columns
  can also receive oversized values.
- **Proposed correction:** persist stable safe messages/codes, use an external id
  or hashed record reference, and use recipe line number as ingredient context.
  Keep reproduction data in the access-controlled raw payload field.
- **Disposition:** **fix now**.
- **Required coverage:** sentinel secret does not appear in logs/errors; external
  id remains available as a safe reference.

### DIA-011 — Non-tolerant mode stops but does not roll back the full run

- **Area:** behavioral edge cases; transaction integrity
- **Severity:** medium
- **Type:** verified defect
- **File / symbol:** `api/src/platewise_api/imports/service.py` — `run_import(tolerant=False)`
- **Verified behavior:** on the first record persistence failure, the service
  marks the run failed and stops, but successful earlier record writes remain in
  the caller's transaction. This differs from the architecture's abort wording
  and a normal reading of non-tolerant behavior.
- **Why it matters:** a caller can commit a `failed` run together with partial
  domain writes.
- **Proposed correction:** wrap domain work in a run-level savepoint; on a
  non-tolerant failure roll it back, then persist a minimal failed run/error in
  the caller transaction.
- **Disposition:** **fix now**.
- **Required coverage:** earlier successful item and hierarchy writes are absent,
  while one failed run and safe structured error remain.

### DIA-012 — Source warnings and suspicious empty payloads are invisible

- **Area:** observability; behavioral edge cases
- **Severity:** low
- **Type:** verified defect
- **File / symbol:** `api/src/platewise_api/imports/sources/base.py` — `FetchResult.warnings`;
  `api/src/platewise_api/imports/service.py` — `run_import`
- **Verified behavior:** `FetchResult.warnings` is never consumed and an empty
  payload completes cleanly without a warning, even though documentation calls
  it suspicious.
- **Why it matters:** adapter diagnostics are dropped and operators cannot
  distinguish an intentionally empty scope from a likely upstream failure.
- **Proposed correction:** convert adapter warnings and unscoped empty results
  into structured warning rows while preserving non-destructive completion.
- **Disposition:** **fix now**.
- **Required coverage:** warnings persist, empty remains non-destructive, and run
  status becomes `completed_with_errors` because review is required.

### DIA-013 — Schema checks do not enforce all calculation invariants

- **Area:** security and data integrity
- **Severity:** low
- **Type:** optional recommendation
- **File / symbol:** `db/src/platewise_db/models/providers.py`,
  `db/src/platewise_db/models/recipes.py`, `db/src/platewise_db/models/catalog.py`
- **Verified behavior:** the database has identity and confidence constraints but
  no checks for positive provider reference/portion grams, non-negative recipe
  grams/quantities, or non-negative nutrition.
- **Why it matters:** application validation protects the importer path, but
  future writers could bypass it.
- **Proposed correction:** add additive check constraints in a future schema
  hardening migration after confirming policy for every write path and existing
  data.
- **Disposition:** **defer**. A schema migration is disproportionate to this
  focused pass because the current importer boundary can reject these inputs and
  the repository has other direct factory/model writers.
- **Required coverage:** migration checks and direct-model constraint tests when
  implemented.

### DIA-014 — Provider matching cannot represent ambiguity

- **Area:** behavioral edge cases; API ergonomics
- **Severity:** low
- **Type:** optional recommendation
- **File / symbol:** `api/src/platewise_api/imports/nutrition/provider.py` —
  `IngredientNutritionProvider.search_food`
- **Verified behavior:** the Protocol returns one food or `None`; multiple
  plausible matches cannot be represented. The fake silently overwrites
  duplicate normalized aliases during construction.
- **Why it matters:** a future real provider must not silently choose among
  ambiguous candidates.
- **Proposed correction:** reject ambiguous fake configuration now; evolve the
  real-provider contract to a typed search result/candidate set when a real
  provider is introduced.
- **Disposition:** **partially fix now** (reject duplicates in the fake);
  **defer** Protocol expansion until a real provider supplies concrete search
  semantics.
- **Required coverage:** duplicate provider id/name/alias rejection.

## Areas verified as sound

- **Architecture:** the synchronous source → contracts → classification → two
  nutrition paths → repository flow matches the approved plan; no competing
  architecture is needed.
- **Provenance:** source-provided and recipe-calculated rows coexist; display
  precedence prefers source nutrition and excludes incomplete calculations.
- **Decimal arithmetic:** calculation uses `Decimal` end to end and quantizes
  only at output/persistence boundaries. The gap is input bounds, not float use.
- **Per-record tolerance:** each item runs in a savepoint and the current tests
  verify failed-record rollback while other records and the error row survive.
- **Historical versions:** meaningful structured recipe changes supersede rather
  than overwrite versions; reversion creates another historical version.
- **Non-destructive imports:** no importer path deletes or deactivates entities;
  malformed and empty inputs do not erase existing records.
- **Test isolation:** database URLs are forced to a `*_test` database unless an
  explicit `TEST_DATABASE_URL` is supplied, and each test rolls back its work.
- **Network isolation:** the shipped fixture source and fake nutrition provider
  are in-memory and make no network calls.
- **Migrations:** no Phase 3 schema change is required for the fixes above.

## Documentation drift identified

- `docs/data-import-architecture.md` says empty payloads complete safely but does
  not describe the review warning added for suspicious emptiness.
- The architecture says `tolerant=False` aborts but does not explicitly state the
  full-run rollback and failed-run persistence contract.
- Provider cache documentation calls the cache reproducible without stating that
  existing provider-food snapshots are immutable in the MVP.
- Phase 2 test counts remain historical in the append-only log and must not be
  rewritten; Phase 3 validation will record the new total separately.

## Implementation boundary

All **fix now** work is a focused behavior hardening or behavior-preserving
refactor. No public HTTP endpoint, frontend, real provider, network access,
background job, external cache, authentication flow, schema migration, or broad
repository refactor is introduced.

## Phase 3 implementation status

Implemented DIA-001 through DIA-007, DIA-009 through DIA-012, the query-reduction
portion of DIA-008, and the fake-provider ambiguity portion of DIA-014. Deferred
only DIA-008's provider snapshot refresh/version policy, DIA-013's future
database check constraints, and DIA-014's real-provider candidate-set Protocol.

Measured evidence: for two repeated provider-ID lookups and two equivalent
normalized-name lookups, the underlying provider call count changed from two per
lookup kind to one per unique key. Provider-food persistence also reuses the
returned ORM primary key per unique food within an item instead of querying it
again for every recipe line.

Final validation: `120 passed, 1 warning`; Ruff passed; Alembic reported no
schema drift; application import and mapper configuration passed; Compose
configuration passed. No migration file or schema model was changed.
