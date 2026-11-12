# Tables: Seat-to-table command contract (2026-11-12, increment 3)

Status: standalone architecture contract; **not** an integrated endpoint or production-ready implementation. Previous increments already covered occupancy projection and its 16-test offline prototype. This increment covers the distinct **Seat** command, not another read projection.

## Command and trust boundary
`POST /venues/{venue_id}/tables/{table_id}/seat` (proposed route, not implemented). Body: `{ "session_id": "opaque-id", "guest_count": 2, "idempotency_key": "opaque-key", "expected_table_revision": 7 }`. The venue and actor MUST be resolved from an authenticated server-side authorization context; reject client-supplied venue claims that conflict with that context. Only roles explicitly granted seating permission may call it. CSRF protections are required for cookie-based sessions. No public API until security gates pass.

## Preconditions and atomic write
1. Validate nonblank identifiers, integer guest count (reject booleans), `guest_count >= 1`, and a bounded input size.
2. Lock the physical table row within a database transaction. Require matching venue, enabled table, positive physical capacity, `guest_count <= capacity`, and matching revision. Never use visual floor-plan dimensions as physical capacity.
3. Require no active seating session on the table and no duplicate session ID; enforce both with database uniqueness constraints, including a partial unique index on `(venue_id, table_id) WHERE ended_at IS NULL` where supported.
4. Record one active seating session and increment table revision in the SAME transaction. On conflict return 409 with a generic code; do not perform a read-then-write without locking/constraints.
5. Scope idempotency records by venue, actor/authorization scope and key. Replays with identical canonical request hash return the same outcome; key reuse with a different payload returns 409. Persist the result transactionally.
6. Emit a synthetic/auditable `table.seated` event via transactional outbox (later phase). Never send guest notifications automatically.

## Response and errors
Successful response: `201 { "session_id": "...", "table_id": "...", "guest_count": 2, "table_revision": 8 }`; exact replay may return 200 with the same identifiers. 400 invalid input; 401 unauthenticated; 403 unauthorized; 404 unknown/not-visible venue table; 409 occupied, stale revision, or idempotency conflict. Avoid exposing other venue inventory through errors.

## Required acceptance tests
- Valid seat and exact-capacity seat; ended session permits new seating.
- Disabled, nonexistent, other-venue, over-capacity, zero/boolean guest count rejected.
- Double seating under simultaneous requests yields exactly one success; second receives 409.
- Same idempotency key same payload returns same session; changed payload rejected.
- Stale revision rejected; rollback leaves no partial session/outbox record.
- No session can be assigned to two tables; no table can have two active sessions.
- Unauthorized/CSRF requests cannot mutate; tenant enumeration does not disclose table details.

## Integration dependencies
Recover actual HORECA source and migration framework; inspect auth, DB engine and prior tables schema. Only then implement route, transaction/constraints, real concurrent integration tests and accessible Seat control. Existing offline occupancy prototype is read-only and cannot itself guarantee atomic seating.

## Safety and scope
Synthetic data only; €0 incremental spend; no payment processor, customer communications, external integration or deployment. Main remains reserved for reviewed integration. This document is a design contract, not proof of a working UI or concurrency-safe backend.
