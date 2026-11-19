# Order → inventory deduction contract (offline design v1)

**Date:** 2026-11-19 (Europe/Brussels)  
**Status:** standalone architecture increment; not wired to a verified HORECA checkout/KDS implementation.  
**Scope:** one idempotent stock-consumption event for a synthetic, accepted order. No payment capture, external communication, or live inventory.

## Trigger and trust boundary

An authenticated, authorized server-side order transition to `accepted` records an immutable `OrderAccepted.v1` event **in the same SQLite transaction** as the order state change. Browser requests and KDS displays must not directly deduct stock. Server-derived `venue_id` and immutable `order_id` are authoritative; reject any client-supplied venue override. A cancelled/rejected order does not emit this event. Amendments/voids require separate compensating events; never edit historical ledger rows.

Event envelope: `event_id` (UUID), `schema_version=1`, `venue_id`, `order_id`, `order_revision` (positive integer), `accepted_at` (UTC ISO-8601), and order lines `[{line_id, menu_item_id, quantity}]` (quantity positive integer). Store a canonical payload hash to detect reused IDs with changed content. No guest identity, card information, or employee health data.

## SQLite persistence and invariants

Use integer **base-unit quantities** (e.g. grams or millilitres) with explicit conversion/rounding rules in the venue-scoped recipe BOM. Never use binary floats for stock. Proposed tables:

- `inventory_outbox(event_id PRIMARY KEY, venue_id, event_type, payload_json, payload_sha256, status, attempts, created_at)`
- `inventory_consumptions(venue_id, event_id, payload_sha256, applied_at, PRIMARY KEY(venue_id,event_id))`
- `stock_ledger(entry_id PRIMARY KEY, venue_id, event_id, order_line_id, ingredient_id, delta_base_units, created_at, UNIQUE(venue_id,event_id,order_line_id,ingredient_id))`

Foreign keys and composite venue-scoped references must prevent cross-venue BOM, menu-item, order or ingredient linkage. For recipe snapshots, persist the resolved BOM revision and per-line ingredient requirements when the order is accepted; do not retroactively deduct a changed recipe. Missing recipe, invalid conversion, nonpositive quantity, or unknown ingredient is an explicit failure awaiting human reconciliation, **not** a silent zero deduction.

## Atomic consumer algorithm

1. Begin `BEGIN IMMEDIATE` transaction and load the outbox event by ID; verify its hash, schema, and server-side venue scope.
2. Look up `inventory_consumptions(venue_id,event_id)`. If present and hash matches, return `already_applied` without writing stock. If the hash differs, reject as an integrity conflict.
3. Validate every line and frozen recipe snapshot, compute exact integer base-unit deductions, and check policy for negative balances (either block or explicitly allow flagged negative stock; never silently clamp).
4. Insert all negative stock-ledger rows, then the consumption marker, and mark the outbox event delivered in **the same transaction**. Commit. On failure roll back every write.
5. On process crash or retry, re-run with the same `event_id`; the unique marker and ledger keys guarantee at-most-once effect. Different event IDs for the same `(venue_id,order_id,order_revision,accepted)` must also be prevented by a producer-side uniqueness constraint.
6. Dispatch only to a local mock consumer. KDS acknowledgement and payment status are not evidence of ingredient consumption.

## Required regression matrix before integration

- First valid event creates exactly the expected negative ledger deltas.
- Identical replay creates zero additional entries and returns `already_applied`.
- Same event ID with different payload hash fails without mutation.
- Concurrent duplicate consumers result in one deduction (separate SQLite connections).
- Wrong-venue ingredient/recipe/order is rejected.
- Missing BOM or conversion overflow rolls back all rows and leaves event retryable.
- Crash after ledger inserts but before marker commit leaves no partial consumption.
- Changed recipe after order acceptance does not alter the frozen deduction.
- Cancellation, amendment, and refunds do not automatically reverse stock; compensations require independently authorized, auditable event types.

## Integration dependency / deployment gate

Before implementation, inspect actual `develop` source for order lifecycle, recipe/BOM and ledger schemas, transaction helpers, migrations and tests. Prioritize the user-directed authenticated Python menu catalog API before any React catalog integration. This document is **not** evidence of a working integration or executed tests. No public backend deployment until session authentication, CSRF, authorization, venue isolation, secrets, and regression gates are verified. No paid services, real orders or real customer data.
