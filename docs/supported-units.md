# Supported Units & Unsupported-Quantity Behavior

How the importer converts recipe ingredient quantities to grams
(`api/src/platewise_api/imports/recipes/units.py`), and what it does when it cannot. All factors
are exact `Decimal`.

## Mass units → grams (direct conversion)

| Unit (aliases) | Grams per 1 unit |
| --- | --- |
| `g` (gram, grams, gm) | `1` |
| `kg` (kilogram, kilograms) | `1000` |
| `mg` (milligram, milligrams) | `0.001` |
| `oz` (ounce, ounces) | `28.349523125` |
| `lb` (lbs, pound, pounds) | `453.59237` |

Conversion is exact and unrounded; the result is quantized (4 dp) only at
persistence.

## Portion / count / volume units → grams (via provider portion)

These units are **recognized** but have no intrinsic gram weight:

`cup`, `tbsp`, `tsp`, `ml`, `l`, `clove`, `slice`, `medium`, `large`, `small`,
`breast`, `piece`.

They convert to grams **only** when the resolved provider food supplies a
matching portion weight (`provider_food_portions`, e.g. `1 cup cooked rice =
158 g`, `1 tbsp olive oil = 13.5 g`). Matching is by exact normalized portion
description. If the provider has no matching portion, the line is
`unsupported_quantity` — PlateWise never guesses a density or portion weight.

## Unsupported / unquantifiable input

The following always produce an explicit status (never a silent zero or a
guess):

| Input | Result |
| --- | --- |
| vague amount — `to taste`, `as needed`, `for frying`, `for garnish` | `unsupported_quantity` |
| missing quantity | `unsupported_quantity` |
| negative quantity | source-contract validation failure |
| unrecognized unit (e.g. `splash`) | `unsupported_quantity` |
| recognized non-mass unit with no matching provider portion | `unsupported_quantity` |
| no provider food match | `nutrition_match_missing` |
| non-nutritive (`water`) | `excluded_non_nutritive` (contributes nothing, not an error) |

Any `unsupported_quantity` or `nutrition_match_missing` line makes the recipe's
calculated nutrition `partial` (not authoritative) and is recorded as a review
warning in `import_errors` (stage `resolve_ingredient`). The ingredient row is
preserved with its original text and status for later review.

## Adding units or portions

* **Mass unit:** add it to `_MASS_UNITS_TO_GRAMS` and `_UNIT_ALIASES` in
  `units.py` with an exact `Decimal` factor.
* **Portion weight:** provide it on the provider food
  (`ProviderFoodData.portions` → `provider_food_portions`), not as a hard-coded
  density. This keeps conversions traceable to a provider record.
