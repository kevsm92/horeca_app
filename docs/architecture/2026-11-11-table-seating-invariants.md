# Tables foundation — seating invariant contract (2026-11-11, 13:00 Europe/Brussels)

Status: architecture contract, **not integrated application code**. The develop branch currently contains only the repository initialization README; previous ZIPs have not been recovered or verified.

## Scope of this increment
A venue owns physical tables. Each table has an immutable identifier, venue_id, positive physical_seats, and active flag. A seating session has immutable id, venue_id, table_id, positive guests and open/closed lifecycle. Physical seat count is not the floor-plan visual size.

The `Seat` command must validate: authenticated venue-scoped permission (future API gate); table belongs to actor's venue; table active; integer guests between 1 and physical_seats; session identifier unused; and no other open session on that table. A session close must be venue-authorized and must not delete the historical session. Reusing a closed session ID is prohibited. Cross-venue table or session access fails closed. UI must not rely on client-side capacity or occupancy state for authority.

## Required database enforcement before API integration
- Composite venue ownership foreign keys: (venue_id, table_id) and (venue_id, session_id), plus a positive physical_seats check.
- Unique partial index on seating_sessions(table_id) WHERE closed_at IS NULL (or equivalent, including venue_id).
- Atomic transaction for seating, including a table row lock or equivalent serialization; catch unique conflicts as 409. Never use a read-then-write check alone.
- Guest count check against locked physical capacity, rejecting boolean/noninteger input; disallow lowering physical_seats below any open session guest count.
- Require server-side authentication, venue authorization, idempotency strategy, immutable audit events and regression tests before public API exposure.

## Local standalone reference verification
A synthetic, standard-library Python reference implementation was run locally on 2026-11-11. Seven unit tests passed: seat/release, double-seating rejection, cross-venue seating rejection, invalid capacity/count rejection, session-ID reuse rejection, cross-venue close rejection and inactive table rejection. Python compilation succeeded. These tests validate the standalone model **only**, not GitHub application integration or concurrency.

## Pending
Recover verified HORECA source and test harness; integrate schema migration and transactional service; add SQLite/PostgreSQL race tests, venue RBAC and Seat-to-table UI on the next dated theme. No deployment, live guest data, payments or external connections.
