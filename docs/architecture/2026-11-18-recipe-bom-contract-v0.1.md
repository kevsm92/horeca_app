# Recipe/BOM v0.1 — venue-scoped mapping contract (2026-11-18)

**Status:** architecture-only, not deployed or integrated. **Scope:** one narrowly bounded recipe-to-ingredient mapping contract; no stock posting, procurement, or customer data.

## Preconditions and trust boundary

The inspected `develop` README describes an initialized repository with historical source archives not recovered. No Python HTTP application or inventory implementation was verified during this run. This specification is therefore not evidence of a functioning recipe service. A future implementation must inspect the current source before adopting these names. The menu-first authenticated Python API requirement remains the immediate integration prerequisite; this document does not authorize a public API.

## Proposed relational model (SQLite)

- `ingredients(venue_id TEXT, ingredient_id TEXT, name TEXT, base_unit TEXT CHECK(base_unit IN ('g','ml','each')), allergen_codes_json TEXT, PRIMARY KEY(venue_id,ingredient_id))`
- `recipes(venue_id TEXT, recipe_id TEXT, menu_item_id TEXT, revision INTEGER CHECK(revision>0), yield_portions INTEGER CHECK(yield_portions>0), status TEXT CHECK(status IN ('draft','approved','retired')), PRIMARY KEY(venue_id,recipe_id,revision))`
- `recipe_lines(venue_id TEXT, recipe_id TEXT, revision INTEGER, line_no INTEGER CHECK(line_no>0), ingredient_id TEXT, quantity_base INTEGER CHECK(quantity_base>0), waste_basis_points INTEGER CHECK(waste_basis_points BETWEEN 0 AND 9999), PRIMARY KEY(venue_id,recipe_id,revision,line_no), FOREIGN KEY(venue_id,recipe_id,revision) REFERENCES recipes(venue_id,recipe_id,revision), FOREIGN KEY(venue_id,ingredient_id) REFERENCES ingredients(venue_id,ingredient_id))`
- `ingredient_cost_quotes(venue_id TEXT, ingredient_id TEXT, quote_id TEXT, cents_per_base_unit_num INTEGER CHECK(cents_per_base_unit_num>=0), cents_per_base_unit_den INTEGER CHECK(cents_per_base_unit_den>0), currency TEXT CHECK(currency='EUR'), valid_from TEXT, PRIMARY KEY(venue_id,ingredient_id,quote_id), FOREIGN KEY(venue_id,ingredient_id) REFERENCES ingredients(venue_id,ingredient_id))`

Enable `PRAGMA foreign_keys=ON` **on every connection**. No cross-venue foreign keys may omit `venue_id`. Treat recipe revisions as immutable once approved; edits create a new revision. Add transactionally enforced single-active-revision rules and scoped menu-item FK only after inspecting the real catalog schema.

## Unit and costing rules

Normalize ingredient input to **integer base units** at the trust boundary: g for mass, ml for volume, each for discrete items. Accept exact integer grams/millilitres/each, or decimal kg/litre converted by exact decimal arithmetic to integer g/ml. Reject fractional base units, nonfinite values, negatives, zero quantities, unknown units, and mass-to-volume conversions without a separately approved ingredient-specific density rule. Never silently infer density. Use integer numerator/denominator for unit cost and explicit half-up rounding **once per recipe total**, not per line. Cost assumptions must retain source, quote date, currency and revision; absent quotes yield `cost_unavailable`, never zero cost.

For line quantity `q`, waste basis points `w`, and rational unit cost `n/d`, planned ingredient cost is `q * 10000 * n / (d * (10000-w))` cents, calculated with exact rational arithmetic. Reject `w=10000`. Total recipe cost sums exact fractions, rounds once to integer cents, then per-portion display divides by `yield_portions` using a documented rounding rule. This is an **estimate**, not a posted inventory movement or financial settlement.

## Allergen provenance

Ingredient allergen codes are controlled EU allergen identifiers, not free-text assertions. Recipe allergen set is the union of current ingredient allergen codes, with a source/revision snapshot on approval. Missing or unverified ingredient allergen metadata yields `allergen_review_required`, never `allergen_free`. Cross-contact and substitutions require separate human-reviewed controls; this contract does not certify allergen safety.

## Security and acceptance scenarios (to implement as automated tests)

1. Venue A recipe cannot reference venue B ingredient, even if IDs coincide; cross-venue joins always include `venue_id`.
2. Foreign-key enforcement rejects an orphan recipe line; concurrent revision approval cannot mutate an approved BOM.
3. `0.125 kg` maps exactly to `125 g`; `0.0005 kg` is rejected rather than rounded to 1 g.
4. A `ml` recipe cannot consume a `g` ingredient without an approved conversion; negative, NaN, infinity, and unknown units fail closed.
5. Missing cost quote produces `cost_unavailable`; repeating identical inputs produces deterministic integer-cent totals.
6. Ingredient with unknown allergens yields review-required; changing ingredient allergens after approval does not silently rewrite the historical approved snapshot.
7. Unauthorized or unauthenticated requests cannot read recipes or select another venue via a supplied venue ID.
8. Fictional fixtures only; no supplier ordering, stock deductions, payment activation, outbound messages, or public deployment.

## Next dependencies

Recover and verify Python/SQLite source and current React catalog state; implement authenticated venue-scoped menu-item persistence and read-only API first. Then translate this contract into migrations, Python domain validation and SQLite transaction tests, with synthetic ingredients and menu items. Review allergen terminology and venue-specific HACCP requirements before production use.
