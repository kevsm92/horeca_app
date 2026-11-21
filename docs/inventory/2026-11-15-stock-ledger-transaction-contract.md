# Inventory foundation: venue-scoped append-only stock ledger (2026-11-15)

Scope: **offline SQLite reference**, not an integrated inventory service. This is the first inventory-foundation milestone under the 2026-11-14 rescheduling; it does not repeat reservation architecture.

## Transaction contract

- Ingredient identity is composite `(venue_id, ingredient_id)`, with an explicit base unit `g`, `ml` or `each`; quantities are integer thousandths of that unit, never binary floating-point.
- Append stock events only; updates and deletes are blocked by database triggers. Reasons: `opening`, `receive_mock`, `consume_mock`, `waste_mock`, `count_adjustment`. Every stock mutation is synthetic and offline.
- `UNIQUE (venue_id, event_key)` enforces idempotency; a repeated key with different ingredient, delta or reason is an error. A replay with an identical payload does not change stock.
- Each write uses `BEGIN IMMEDIATE` and validates venue-owned ingredient existence and `SUM(delta_milli) + new_delta >= 0` before inserting. A failed transaction rolls back. This serializes competing SQLite writers, preventing double consumption of the last unit.
- Queries always include `venue_id`; database foreign keys use composite venue and ingredient IDs. An application must additionally enforce authenticated venue membership and RBAC before exposing any API.
- Disallow zero, non-finite, excess-precision or unbounded quantities. Count corrections are new signed events; historical entries remain immutable.
- Physical stock checks, lot expiry, recipe conversions, receiving provenance, opening-date label linkage, stock count authorization, human correction workflows and event audit metadata are later milestones.

## Locally exercised reference

Two supplemental files were produced and executed in a temporary environment: `inventory_ledger_sqlite.py` and `test_inventory_ledger_sqlite.py`. Command: `python -m unittest -v test_inventory_ledger_sqlite.py`. Result: **8 tests passed**, including two concurrent SQLite consumers competing for one unit; exactly one succeeds. Other tests cover venue isolation, duplicate retry/payload mismatch, rollback on insufficient stock, append-only triggers, invalid decimal precision and nonfinite values, and invalid reasons.

**Limitation:** this documentation commit does not itself persist those executable files. Their local test result is not a claim of remote CI or deployed behavior. Next action: commit the executable reference and regression tests, then add append-only provenance and controlled stock corrections before any application integration.

Safety: €0 new spending, no supplier orders, payment services, customer/staff records, camera capture, external messaging or deployment. `main` remains the reviewed baseline.
