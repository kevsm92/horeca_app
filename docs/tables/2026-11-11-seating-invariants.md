# Tables foundation — seating invariants (2026-11-11)

Status: architecture contract only. The repository currently contains an initialization README, not a recovered application. This document is not evidence of a deployed API or implemented persistence.

## Scoped milestone: venue-owned physical table and active seating contract

Tables: `physical_tables(venue_id, table_id, capacity_seats, active, revision)`, primary key `(venue_id, table_id)`, `capacity_seats INTEGER NOT NULL CHECK(capacity_seats >= 1)`. Capacity is physical inventory, **not** the floor-plan drawing size.

Sessions: `seating_sessions(venue_id, session_id, table_id, guest_count, state, opened_at_utc, closed_at_utc)`. Composite foreign key `(venue_id, table_id)` references physical tables; primary key `(venue_id, session_id)`. `state IN ('active','closed')`; `guest_count INTEGER NOT NULL CHECK(guest_count >= 1)`. Enforce one active session per physical table using a partial unique index on `(venue_id, table_id) WHERE state = 'active'`. Never silently reuse an active session ID.

## Atomic Seat command

Authenticated actor with explicit venue authorization requests `seat(venue_id, table_id, session_id, guest_count)`. In one database transaction, lock the venue-owned table row, require `active = true`, require `1 <= guest_count <= capacity_seats`, insert the active session and commit. Unique-index collisions are conflicts, not retries that create extra sessions. Never trust a venue ID from the browser without comparing it to the authenticated scope. The Seat button must select an actual physical table; no unassigned 'seated' state.

Closing requires an authorized actor and an existing active session in the same venue; preserve closed session history. Seat capacity cannot be reduced below active guest count. Changing floor-plan dimensions never changes physical capacity.

## Synthetic acceptance matrix

1. Four guests at a four-seat active table: accept.
2. Five guests at a four-seat table, zero, negative, fractional or boolean guest count: reject.
3. Concurrent seats for the same venue/table: exactly one succeeds.
4. Same table ID in two venues: isolated; no cross-venue access.
5. Missing or inactive physical table: reject.
6. Duplicate session ID in one venue: reject; closed session ID remains reserved.
7. Close then seat a new session: accept; retain the old closed record.
8. Reduce capacity below active guest count: reject.
9. Retry after a lost response: use a separately designed request idempotency key; do not create another active session.

## Verification and limits

A separate offline Python standard-library reference model was executed in this run with **6 passing unittest methods** (valid seating, capacity, duplicate seating/reopening, venue isolation, duplicate IDs, inactive/invalid inventory). This document itself has no executable tests in the repository. No production database, migration, API authentication or concurrent transaction test is verified. Next increment: implement this contract against the recovered application and run actual SQLite/PostgreSQL concurrency and tenant-isolation tests.

No real guest data, paid services, integrations or deployment.