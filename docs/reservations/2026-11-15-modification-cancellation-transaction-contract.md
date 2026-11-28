# Reservation modification/cancellation transaction contract (2026-11-15, 17:00 Europe/Brussels)

Scope: offline architecture only. The existing `prototypes/reservation_availability.py` covers read-only availability; this increment specifies **atomic modification and cancellation**, without claiming implementation.

## Model
`reservation(id, venue_id, table_id, party_size, start_utc, end_utc, status, version, updated_at_utc)`. Statuses: `confirmed`, `seated`, `completed`, `cancelled`, `no_show`. Use aware instants and persist UTC. Venue policy supplies turnover, booking horizon and permitted cancellation window; never hardcode legal rules. Table belongs to same venue and capacity is at least party size. A seated reservation cannot be moved or cancelled by this endpoint; use a separate manager-reviewed operational flow.

## Mutation protocol
1. Authenticate principal; authorize `reservations:write` for venue from server-side membership, not request-supplied venue claims.
2. Begin database transaction. Lock reservation and candidate physical table rows in stable ID order (or use serializable isolation with bounded retries). Verify same venue, active table and immutable reservation identity.
3. Require `If-Match`/expected integer `version`; stale version returns 409, no write. Require an idempotency key scoped to (venue, principal, operation) with request-payload digest; same key/digest returns original outcome, same key/different digest returns 409.
4. For modification, validate party size, UTC interval, policy, table capacity, and overlap against all confirmed/seated reservations for the candidate table, excluding the reservation being changed. Treat intervals as half-open; include configured turnover. Serialize all writers for the table, including creates and seat actions, to avoid write skew.
5. For cancellation, allow only confirmed reservations and apply documented venue cancellation policy. Set status cancelled without deleting the historical record; cancelled reservations no longer block availability. Do not send customer communications.
6. Atomically persist version+1, immutable audit event (actor, venue, old/new values, UTC timestamp, reason), and mock-only outbox event. Commit once. On rollback, neither audit nor outbox is emitted.
7. Read endpoints always scope by authorized venue and must not reveal cross-venue existence (use 404 where appropriate).

## Required regression tests before API activation
- Two concurrent modifications target the last free table: exactly one commits; loser receives conflict.
- Simultaneous booking creation and modification of same table: no overlapping confirmed records.
- Cross-venue table ID and reservation ID are rejected, with no audit or outbox event.
- Capacity 2 cannot accept party 3; disabled table cannot accept bookings.
- Cancelled booking frees slot; repeated cancellation with same idempotency key is stable.
- Stale expected version, changed payload under reused key, invalid timezone and reversed interval fail closed.
- Seated/completed reservations cannot be silently cancelled or modified.
- Audit and outbox are atomic with mutation; failed transactions leave no partial effects.
- Synthetic-only fixtures, no real guest identifiers or notifications.

## Limitations and next dependency
The GitHub repository's verified prototype is read-only; no database, transaction locks, authenticated route or migration has been verified in this milestone. This document is **not** a working booking API and does not establish double-booking prevention. Implement a database-backed mutation with a shared locking strategy and run race tests before exposing reservation writes. No deployment, paid services, messages or real data.
