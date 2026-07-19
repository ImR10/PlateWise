# Recipe → Nutrition Calculation

How PlateWise turns a structured recipe into per-serving nutrition, and the
integrity rules that keep the result honest. See also
[data-import-architecture.md](data-import-architecture.md) and
[supported-units.md](supported-units.md).

## Pipeline

```
recipe ingredient line
   → parse   (parser.py)      quantity, unit, name, preparation, raw/cooked
   → resolve (resolver.py)    provider food + grams + resolution status
   → aggregate (calculator.py) Σ contributions, ÷ servings → per-serving
```

### 1. Parse (`recipes/parser.py`)

Uses the source's structured fields when present; otherwise conservatively
parses `original_text` for a leading quantity (integer, decimal, or simple/mixed
fraction like `1/2`, `1 1/2`), a recognized unit token, the ingredient name, and
a preparation note (from a parenthetical or a trailing `, diced`). A missing or
unparseable quantity stays `None` — it is never invented.

### 2. Resolve (`recipes/resolver.py`)

Maps a parsed line to a canonical provider food and a gram weight. Outcomes
(`IngredientResolutionStatus`):

| Status | Meaning |
| --- | --- |
| `resolved` | matched a provider food **and** has a trustworthy gram weight — the only status that contributes nutrition |
| `excluded_non_nutritive` | e.g. water — intentionally contributes nothing (not an error) |
| `unsupported_quantity` | vague ("to taste"), missing quantity, or a unit with no gram conversion |
| `nutrition_match_missing` | no provider food matched |
| `needs_review` | default until resolved |
| `invalid` | unusable line |

Food matching is deterministic: by `external_food_id` (confidence 1.00) or exact
normalized name/alias search (0.80). Fuzzy matching is never authoritative.

### 3. Aggregate (`recipes/calculator.py`)

For each **resolved** ingredient and each nutrient:

```
contribution = provider_per_reference_value × grams ÷ reference_grams   (reference_grams = 100)
recipe_total = Σ contributions
per_serving  = recipe_total ÷ servings
```

## Integrity rules (enforced + tested)

* **Missing nutrient ≠ zero.** If any contributing food lacks a nutrient, that
  nutrient's recipe total is `NULL` (unknown), never summed as zero.
* **Unresolved ingredient ≠ zero.** An unresolved (non-excluded) line makes the
  calculation `partial`; its absent contribution is not counted as zero.
* **No guessed quantities.** Vague/unsupported amounts stay unresolved.
* **Servings required.** Missing/zero servings ⇒ `failed` (no per-serving basis);
  negative servings fail source-contract validation.
* **Non-negative finite inputs.** Negative, `NaN`, infinite, or SQL-overflowing
  nutrients/quantities are rejected before calculation or persistence. Provider
  reference grams and portion weights must be strictly positive.
* **Partial is retained but not authoritative.** Subtotals from resolved lines
  are still stored (for review), but `is_complete = false` and
  `review_status = needs_review`, so `display_nutrition()` will not use them.

`calculation_status`:

| Status | Condition |
| --- | --- |
| `complete` | all lines resolved/excluded, servings valid, every nutrient known → authoritative |
| `partial` | some line unresolved, or some nutrient unknown |
| `failed` | no contributing ingredient, or servings missing/≤0 |

## Traceability

Every calculated value is traceable to: the **recipe version** (`recipe_versions`,
versioned by content hash — a recipe change creates a new version, preserving
history), each **ingredient line** (`recipe_ingredients`: original text, parsed
quantity/unit, grams, `resolution_status`, `match_method`, confidence), the
**resolved provider food** (`provider_foods` + `provider_food_portions`), and the
**calculation version** (`nutrition_facts.calculation_version`, `calculated_at`,
`recipe_version_id`).

## Decimal precision & rounding (`recipes`/`decimal_utils.py`)

All quantity, gram, and nutrient arithmetic uses `decimal.Decimal` — never binary
float. A source `float` is routed through `str` so `0.1` is `Decimal("0.1")`.

| Value | Precision (SQL) | Quantize |
| --- | --- | --- |
| nutrients | `Numeric(10, 2)` | 2 dp |
| grams / parsed & normalized quantities | `Numeric(12, 4)` | 4 dp |
| serving sizes | `Numeric(10, 3)` | 3 dp |
| provider per-100 g nutrients | `Numeric(12, 4)` | — |

* **Rounding mode:** `ROUND_HALF_UP`, everywhere.
* **When:** only at persistence/output boundaries. Intermediate sums and the
  per-serving division are computed at full `Decimal` precision and quantized
  once at the end.
* **Serialization:** contracts and provider data expose `Decimal` fields
  (Pydantic v2); structured error `detail` serializes Decimals via `str(...)`.
* **Equality in tests:** compare quantized `Decimal` values (e.g.
  `== Decimal("200.00")`), never floats.

### Worked example

`6 oz chicken` + `1 tbsp olive oil`, 2 servings, provider values per 100 g
(chicken 165 kcal, oil 884 kcal; 1 tbsp oil = 13.5 g):

```
chicken: 6 oz × 28.349523125 = 170.09713875 g → 170.09713875 × 165 / 100 = 280.66... kcal
oil:     13.5 g                                → 13.5 × 884 / 100          = 119.34    kcal
total = 400.00 kcal → per serving = 400.00 / 2 = 200.00 kcal
```

## Explicitly out of scope (MVP)

Cooking-loss/yield modeling, oil-absorption estimation, interpreting "to taste",
volume→gram conversion without a resolved provider portion, and any real
external nutrition provider. Unresolved cases are preserved for review, never
guessed.
