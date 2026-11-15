# Reservation availability contract v0.1 — 2026-11-15

Status: **architecture-only**. The remote `develop` branch has a repository README but no verified reservation implementation. This is a proposed contract, not deployed code or evidence of passing application tests.

## Scope of this increment
A venue-scoped, table-aware **availability decision** for a single requested interval. Booking writes, waitlists, guest notifications and payment are out of scope.

### Inputs
`venue_id`, `party_size` (positive integer), `starts_at` (timezone-aware instant), `duration_minutes` (positive), `turnover_minutes` (nonnegative), and optional `excluded_reservation_id` for a modification. Resolve venue-local opening rules using the venue's IANA timezone (e.g. Europe/Brussels); store all instants in UTC. Ambiguous/nonexistent local wall times must be rejected or explicitly disambiguated before converting to UTC.

### Authoritative records
- `physical_tables(id, venue_id, active, seat_capacity)`: positive physical capacity, not UI visual dimensions.
- `reservations(id, venue_id, table_id, party_size, start_utc, end_utc, turnover_end_utc, status, revision)`.
- `seating_sessions(id, venue_id, table_id, guest_count, started_utc, ended_utc)`.
- Venue booking rules: opening hours, min/max party, lead time, max advance horizon, permitted durations and configurable turnover. Do not invent default legal or operating values.

### Decision procedure
1. Authenticate principal and authorize the target venue before reading table inventory or bookings. Never accept a client-supplied venue identifier as sufficient authorization.
2. Validate request, rules, physical capacity, and timezone conversion. Calculate `requested_end = starts_at + duration`, `requested_turnover_end = requested_end + turnover` using instants.
3. Consider only active physical tables belonging to the venue with `seat_capacity >= party_size`. This v0.1 contract assumes **one table per reservation**; table combinations require a separate inventory-safe design.
4. Reject a candidate when any same-venue, same-table reservation with blocking status (`confirmed`, `seated`) overlaps the protected window using half-open intervals: `existing.start_utc < requested_turnover_end AND requested.start_utc < existing.turnover_end_utc`. Ignore only the same reservation identified by `excluded_reservation_id` **after** verifying that it belongs to the venue and is modifiable.
5. Reject a candidate if an active seating session occupies that table. A session is active when `ended_utc IS NULL`; never infer vacancy merely from reservation end time.
6. Return eligible table IDs and a rule-version identifier; do **not** promise a booking or disclose other venues' occupancy.

### Write-time concurrency invariant (mandatory before booking API)
A positive availability response is advisory only. On create/modify, reauthorize the venue, lock the venue/table allocation scope (or use serializable transaction plus retry), recheck the **same** rules and protected intervals, and atomically insert/update with revision CAS and idempotency key scoped to venue + principal + operation. A uniqueness constraint on `(venue_id, table_id, start_utc)` alone is insufficient for overlapping intervals. For PostgreSQL, a same-venue/table exclusion constraint over a stored protected `tstzrange` for blocking statuses is a useful defense in depth; SQLite needs an explicit serialized writer strategy. Conflict returns a safe 409; no partial bookings. Never release a seated table without explicit session close.

### Negative/regression cases to implement
1. Adjacent half-open intervals accepted when turnover windows do not overlap.
2. One-minute overlap rejected; turnover overlap rejected.
3. Party exceeds actual physical seats rejected, even when floor-plan shape appears larger.
4. Same table ID in different venues cannot leak data or block the other venue.
5. Cross-venue exclusion ID rejected; cancelled reservations do not block.
6. Active seating session blocks; ended session does not.
7. Simultaneous competing booking transactions: exactly one commits, the other conflicts.
8. Stale modification revision conflicts without changing original booking.
9. DST gap/overlap requires explicit resolution; UTC stored instants remain ordered.
10. Idempotent retry returns same booking result without duplicate allocation.

## Follow-up dependencies
Implement migrations and pure availability evaluator against recovered, verified application source; then transactional create/modify/cancel, tests with real database concurrency, RBAC negative tests, and offline synthetic UI fixtures. Do not expose a public backend or collect real guest data until authentication, CSRF, venue isolation, secret hygiene and test gates pass.

Cost and safety: €0 additional spend; no paid/metered services, payment activation, guest communication, external bookings, or deployment. This specification is not evidence of Belgian regulatory compliance.
