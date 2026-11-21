# Inventory ledger reason/sign integration contract — 2026-11-17 (v0.1)

**Scope:** offline, synthetic-only SQLite inventory prototype. This is an implementation-ready integration contract, not a claim of deployed enforcement.

## Verified starting point

`prototypes/inventory/inventory_ledger.py` already implements venue-scoped ingredients, integer base units, immutable events, idempotency, `BEGIN IMMEDIATE` serialization and nonnegative stock. `prototypes/inventory/stock_reason_policy.py` independently validates signed reasons but explicitly states it is **not wired into the ledger**. The current `post_event` accepts e.g. negative `receipt` and positive `waste`; it also accepts `correction` without provenance.

## Next minimal code change

1. Extend `post_event(db, venue, ingredient, event, delta, reason, *, correction_reference=None)` with a keyword-only correction reference. Call `validate_stock_movement(delta, reason, correction_reference=correction_reference)` **before** `BEGIN IMMEDIATE`.
2. Add nullable `correction_reference TEXT` to new SQLite schema and a migration for existing local databases. Existing events must remain unchanged and auditable; no destructive table replacement. Record a correction only if its referenced event exists **in the same venue and ingredient**. Do not require the referenced event to be a correction. Reject self-reference.
3. For an idempotent retry, compare `ingredient_id`, `delta`, `reason` **and** `correction_reference` under the same `BEGIN IMMEDIATE` transaction. Exact retries return `False`; mismatches raise and roll back. This prevents reusing an event ID with different correction provenance.
4. Keep nonnegative-balance checking and insert in the same write transaction; preserve `stock_no_update` and `stock_no_delete` triggers. Do not accept caller-supplied `created_at` as authoritative.
5. Avoid importing `stock_reason_policy` through ambient current-directory assumptions: make the prototype importable as a package or use an explicit package import in tests.

## Synthetic acceptance cases

| Scenario | Expected |
|---|---|
| receipt +100 g, use -20 g | balance 80 g |
| receipt -1 g | reject, no event |
| waste +1 g | reject, no event |
| correction +5 g referencing same-venue ingredient event | append, balance 85 g |
| correction without reference | reject |
| correction referencing other venue or ingredient | reject |
| correction referencing itself | reject |
| same correction event ID and identical reference retried | return False, one row |
| same event ID but different reference | reject, original row unchanged |
| two concurrent uses each -70 g against 100 g | exactly one succeeds, never negative |
| UPDATE/DELETE stock event | trigger aborts |

## Boundaries and dependencies

This contract does not authorize inventory API access. Authenticated venue/role checks must occur at the service boundary; a venue ID argument alone is not authorization. No actual stock, supplier, payment, or camera data. Future work should implement the migration and tests against a temporary SQLite database, then separately assess legacy invalid-sign events without rewriting the append-only ledger. Never report historical corrections as evidence of a physical stock count without an independently recorded count.
