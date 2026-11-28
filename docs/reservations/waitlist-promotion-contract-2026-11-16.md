# Reservation waitlist promotion — offline contract v0.1
Date: 2026-11-16 (Europe/Brussels). Scope: one deterministic, venue-isolated waitlist promotion decision. This is a design contract, **not** an integrated booking service.

## Inputs
A candidate has `venue_id`, `entry_id`, `party_size` (positive integer), `requested_start` (timezone-aware instant), `duration_minutes` (positive), `created_at` (timezone-aware instant), `status` (WAITING/OFFERED/CONFIRMED/CANCELLED/EXPIRED), and an optional `offer_expires_at`. A physical table has `venue_id`, `table_id`, `capacity` (positive), `active`, and a set of confirmed/held intervals. Policy supplies turnover minutes, venue timezone, offer TTL, and an explicit booking horizon. All instants must be normalized to UTC for comparison; retain the original venue timezone for presentation. No PII is needed for this decision.

## Decision algorithm
1. Within one database transaction, acquire a venue-scoped advisory/row lock (or serialize through an equivalent durable queue); reload all candidates, table inventory, and overlapping confirmed/held reservations from authoritative storage. Reject cross-venue references and malformed timestamps. No client-supplied availability is authoritative.
2. Filter WAITING entries whose requested interval falls within the booking horizon. Sort by `(created_at, entry_id)` ascending; stable order is mandatory, including ties. Do not skip a candidate merely to prioritize a higher-spend guest. A venue may separately document accessibility accommodations and explicit, reviewed priority policy.
3. For each candidate, consider only active physical tables belonging to that venue with `capacity >= party_size`. A candidate interval is `[requested_start, requested_start + duration + turnover)`. A table is available only if it does not overlap any confirmed reservation, unexpired offer hold, or active seating session. Use half-open intervals: `a.start < b.end and b.start < a.end`.
4. Select a fitting table deterministically by `(capacity, table_id)`. If none fits, leave the candidate WAITING; continue evaluating others only where doing so cannot override documented fairness policy.
5. Atomically create a uniquely keyed offer hold `(venue_id, entry_id, offer_generation)` and change the entry to OFFERED, with an expiry computed from a trusted server clock. Database uniqueness must prevent simultaneous overlapping table holds; use a serializable transaction or equivalent locking and conflict retry. Publish only a **mock** notification to an offline outbox. Never contact a guest.
6. Accept an offer only with venue-scoped authorization and a matching, unexpired offer generation; atomically revalidate capacity, occupancy and conflicts before converting to CONFIRMED. Expired offers become EXPIRED, release their hold, and require a new explicit waitlist decision; they must never silently become confirmed. Cancellation is idempotent and audit logged.

## Required invariants / acceptance scenarios
- Two venues may use the same local table ID without seeing or affecting each other's candidates or holds.
- Two concurrent promotions for the same table/time produce **at most one** live hold; a losing transaction retries from fresh state.
- An occupied table or confirmed booking blocks overlapping offers; adjacent half-open intervals may be accepted after the configured turnover.
- A party of five cannot receive a four-seat table; no synthetic merge may create physical seats.
- Replaying a promotion event with the same idempotency key does not create another hold or outbox message.
- A stale acceptance, mismatched generation, cancelled entry, expired offer, or foreign-venue actor fails closed.
- DST ambiguous/nonexistent local times require explicit offset or are rejected; do not silently interpret naive local timestamps.
- No-show is a separate explicit, authorized state transition with audit reason and configurable grace period, never inferred automatically from absence of a check-in event.
- Outbox payloads contain opaque IDs only, no guest contact details; mock delivery remains offline.

## Next implementation dependency
Recover and verify actual reservation/table schema, migrations, transaction strategy, and test runner from the source before implementing this contract. Add database-level overlap protection and concurrency tests, then an offline outbox adapter. No deployment or real messages.
