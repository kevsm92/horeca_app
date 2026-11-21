# Inventory correction provenance gate — 2026-11-17 (v0.1)

**Scope:** one bounded architecture milestone. This is a design/acceptance contract, **not** an implemented migration, tested integration, or production approval.

## Verified develop baseline (7150601dc45a2c12669adb074855643ea44fce6e)

- `prototypes/inventory/inventory_ledger.py` has venue/ingredient composite keys, integer base units, immutable event triggers, idempotency and nonnegative balance checks. Its `post_event` accepts `reason='correction'` without an original-event reference.
- `prototypes/inventory/stock_reason_policy.py` independently requires `correction_reference` for corrections but explicitly says it is **not wired into SQLite ledger**.
- `prototypes/menu/menu_catalog.py` is a separate venue-scoped fictional food/drink catalog. No recipe/BOM or sale-to-stock deduction may be assumed from a menu read.

## Next implementation contract

1. Add nullable `correction_of_event_id` to stock events via an idempotent migration; require it for new correction events and forbid it for receipts, use and waste. For existing rows, do not invent historical references: mark legacy unreferenced corrections as requiring review.
2. Require the referenced event to exist in the **same venue and ingredient**, and reject self-reference, corrections of corrections unless a documented explicit policy permits them, and any reference to an event from another tenant.
3. Preserve the original event unchanged. Record a distinct correction event with its own idempotency key and signed integer delta. A correction that would drive balance negative must roll back atomically.
4. Extend duplicate-key equivalence to include the correction reference; identical retry is no-op, differing reference is conflict. Use `BEGIN IMMEDIATE` and parameterized SQL on a connection with foreign keys enabled.
5. Keep correction author/approval provenance as a future authenticated staff workflow; do not accept arbitrary actor identity from HTTP headers. No HTTP write route is authorized by this contract.

## Required regression matrix before code commit

- Same-venue/same-ingredient valid correction; positive and negative deltas.
- Missing reference, unknown reference, cross-venue reference and cross-ingredient reference all reject without writes.
- Duplicate event ID with same payload returns no-op; same ID with altered reference rejects.
- Concurrent correction vs consumption cannot produce negative stock.
- Trigger rejects UPDATE/DELETE of original or correction events.
- Legacy migration is repeatable and preserves balances; no fabricated historical references.
- Tests execute against actual fetched `develop` source; record command, Python version, counts and failures.

## Dependencies and limits

Do not couple menu item IDs directly to ingredient IDs. Recipe/BOM mapping, quantities, units and a trusted order event must exist before stock deduction. No real stock, guests, supplier orders or external services. Remain offline; public API deployment is blocked pending verified authentication, CSRF, tenant isolation, authorization and hosting safety.
