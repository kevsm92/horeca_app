# Reservation availability and concurrent booking — contract v0.1

**Date:** 2026-11-15 (Europe/Brussels)  
**Status:** Design-only, not implemented or production verified.  
**Scope:** One venue's physical-table reservation availability and atomic booking. This is an independent specification because the reachable `develop` branch contains only the repository initialization README; no recovered application code or runnable tests were available.

## Domain and trust boundaries

- `organization_id`, `venue_id`, `table_id`, `reservation_id` are immutable opaque IDs. A physical table belongs to exactly one venue and has a positive integer `physical_seat_capacity`.
- The authenticated principal must have explicit access to the requested organization and venue. **Never trust venue identifiers supplied by the client without checking membership and role server-side.** All reads and writes are scoped by both organization and venue.
- Reservation fields: `party_size` (positive integer), `start_at` (UTC instant), `end_at` (UTC instant), `status` (held, confirmed, seated, cancelled, expired, no_show, completed), `table_id`, `revision`, `created_at`, `updated_at`, `idempotency_key` (unique within venue and caller scope).
- Store instants in UTC; accept IANA venue timezone for local input/output. Reject nonexistent DST wall times and require explicit offset/fold for ambiguous times. No real guest contact information is needed in the prototype.
- A venue-configured turnover buffer extends the blocked interval after `end_at`. The booking interval is half-open: `[start_at, end_at + turnover_buffer)`. The end must be strictly later than the start; buffer must be nonnegative and bounded by venue policy. Do not hardcode a universal dining duration.
- `held`, `confirmed`, `seated` block capacity; `cancelled`, `expired`, `no_show`, `completed` do not. Expiry and no-show are explicit audited state transitions, never implicit assumptions from clock time.

## Availability query

1. Authenticate and authorize venue access before any query. Return no data for unauthorized venues.
2. Load only active, bookable physical tables belonging to the authorized venue, with capacity >= party size; exclude removed/maintenance tables.
3. Exclude tables whose blocking reservations overlap the requested buffered interval: `existing.start_at < requested.end_at_with_buffer AND requested.start_at < existing.end_at_with_buffer`.
4. Exclude tables occupied by a conflicting active seating session, even when there is no reservation.
5. Return candidate table IDs and capacity; availability is **advisory**, not a guarantee of booking. Do not expose other guests' reservation details.

## Atomic create / modify

The server repeats all availability and authorization checks **inside one database transaction**. In PostgreSQL, serialize conflicting changes by locking the physical table row (`SELECT ... FOR UPDATE`) before checking active reservations and seating sessions; all booking and seating writers must acquire the same table lock. Lock ordering for any multi-table operations must be deterministic. A database-level exclusion constraint on overlapping buffered intervals is recommended as a second line of defense, with the buffer end materialized and enforced for blocking states. Retry serialization/deadlock failures with bounded backoff; never retry authorization failures.

- Create: enforce capacity, valid interval, current table status and conflict-free booking; persist booking plus audit event atomically.
- Modify: require expected `revision` (optimistic concurrency), recheck capacity and conflicts for the proposed table/time, exclude only the reservation being modified, increment revision and append audit record. Reject stale revision with 409.
- Cancel: authorized transition to `cancelled`, preserving history and audit. A repeated cancel with the same idempotency key returns the original outcome; a conflicting payload under the same key is rejected.
- Reservation confirmation does not itself seat guests. Seating requires its own transaction and physical-table capacity/double-seating check.

## Error contract

`400` malformed interval/party size; `401` unauthenticated; `403` unauthorized venue; `404` inaccessible table or reservation (avoid cross-tenant enumeration); `409` overlap, stale revision, already-seated conflict, or reused idempotency key with different payload; `422` capacity/policy violation. The API must never claim a confirmed booking until the transaction commits.

## Executable acceptance scenarios to implement once source is recovered

| ID | Scenario | Expected result |
|---|---|---|
| R01 | Party of 5 requests a 4-seat physical table | Reject 422 |
| R02 | Two concurrent creates for the same table and overlapping intervals | Exactly one commits; other returns 409 |
| R03 | Intervals touch exactly at buffered boundary | Both permitted |
| R04 | Reservation overlaps only turnover buffer | Reject 409 |
| R05 | Cancelled booking occupies the interval | New booking permitted |
| R06 | Existing active seating session overlaps | Reject 409 |
| R07 | Principal from tenant A requests tenant B table ID | No B data returned; reject 403/404 |
| R08 | Concurrent modification with same prior revision | One succeeds; other returns 409 |
| R09 | Identical idempotency key and payload repeated | Return same reservation, no duplicate |
| R10 | Same idempotency key with changed payload | Reject 409 |
| R11 | DST nonexistent/ambiguous local timestamp | Reject or require explicit disambiguation |
| R12 | No-show/expiry without explicit audited transition | Remains blocking |
| R13 | Table marked out-of-service during booking | Atomic conflict rejection |
| R14 | Concurrent seat and reserve for same physical table | At most one conflicting allocation succeeds |

## Integration dependencies and release gate

1. Recover and verify the actual HORECA app, migrations and test harness before integrating this contract; do not assume prior ZIP sprint output exists in GitHub.
2. Introduce venue-scoped schema, physical table inventory and transaction-locking convention shared with seating.
3. Implement repository/API operations and the 14 synthetic acceptance tests, including true parallel database transactions (not just sequential mocks).
4. Verify tenant isolation, capacity and race conditions against the target database engine before exposing any endpoint.
5. No deployment, live guests, communications, payment activation or paid services. Budget: **€0 additional spend**.

**Completion record:** This increment documents the reservation conflict/concurrency contract only. It does not claim working reservations, tests, a deployed API or recovered source.
