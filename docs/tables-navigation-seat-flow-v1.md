# Tables navigation and Seat assignment contract — v1
Date: 2026-11-12 (Europe/Brussels). Status: standalone design, NOT implemented.
Scope: one milestone — define the guarded Seat-to-physical-table flow and its navigation/read-model contract. Floor-plan editing and resizing are deliberately deferred.

## Recovery and constraints
At this run, the reachable `develop` README states historical ZIP sources are not present. No application source, database schema, authentication layer, or runnable tests were verified. Do not represent this document as an integrated feature. All examples below are fictional. No external services or deployment.

## Navigation
Add a top-level **Tables** tab, distinct from Reservations, Orders and QR ordering. Route `/venues/:venueId/tables` is authenticated and venue-authorized. Its first panel is a read-only floor-plan prototype; each table tile displays its physical label, seats, occupied guest count and one of:
- `available`: active seating count 0, table enabled.
- `occupied`: exactly one active seating session.
- `unavailable`: table disabled for service, with no active seating.
- `conflict`: inconsistent legacy data (e.g. multiple active sessions); block seating and raise manager review, never silently pick a session.

The read model is derived server-side from venue-scoped physical tables and active sessions; the browser cannot submit occupancy status as authority. Empty state: “No physical tables configured”; do not fabricate seats. Floor-plan coordinates are optional; missing coordinates use a deterministic non-persisted grid layout. Provide an accessible table list alternative with keyboard-operable Seat controls and text occupancy.

## Seat flow
From a reservation or walk-in card, **Seat** opens a chooser of *existing, enabled, available, venue-owned physical tables* with capacity >= requested guest count. Show each label, physical capacity and status. The chosen table ID is mandatory; never assign an arbitrary placeholder table. Do not automatically combine tables in v1. Reservation venue must equal authenticated venue. Guest count must be a positive integer and may not exceed the chosen table's physical seats. Seat is disabled if the reservation is already seated or cancelled.

Proposed request: `POST /venues/{venue_id}/seatings` with JSON `{ "table_id": "t-01", "reservation_id": "r-01", "guest_count": 3, "idempotency_key": "opaque-client-generated" }`. Walk-ins omit `reservation_id` and provide a server-issued walk-in intent instead; do not accept untrusted free-form guest identity. Authentication, CSRF protection and role authorization are prerequisites to exposing the route. Validate all venue-scoped references on the server. Never trust a venue ID merely because it is in the URL.

Inside one database transaction: lock or otherwise serialize the physical table and referenced reservation, revalidate capacity/availability/venue and idempotency, insert exactly one active session, and bind the reservation. Enforce a database uniqueness constraint for one active seating session per physical table, plus one active seating per reservation. A duplicate idempotency key with identical payload returns the original result; a different payload returns 409. A losing concurrent seating request returns 409 with fresh availability; never double-seat. On successful commit return 201 with session ID, physical table ID, guest count and derived `occupied` status. No downstream order or payment is created.

## UI behavior and accessibility
After 201, navigate to the Tables tab and focus the newly occupied table heading; announce success in a polite live region. On 409, retain the original reservation context, announce conflict and refresh choices. On 403 or 404, reveal no other venue's table metadata. On network timeout, query the idempotency result before retrying; never issue a new key blindly. Table tiles have labels and keyboard focus; color is not the only status signal.

## Acceptance scenarios (synthetic, to automate when source is restored)
1. Venue A, table A1 (4 seats), 3 guests -> 201 and one active seating; Tables tile occupied 3/4.
2. Same key and payload repeated -> same session, no duplicate; same key with changed table -> 409.
3. Concurrent 3-guest attempts on A1 -> one 201, one 409; exactly one active session.
4. Venue B table ID passed in venue A request -> 404 or 403; no cross-venue data disclosure.
5. 5 guests on 4-seat A1, zero guests, disabled table -> validation/conflict, no mutation.
6. Cancelled or already seated reservation -> no new seating; no active session duplication.
7. Absent physical tables -> empty state; Seat offers no fake table.
8. Missing/invalid CSRF or unauthorized staff role -> reject before mutation.
9. Keyboard-only user can select a table and understand occupied/available/conflict states.
10. Inconsistent legacy duplicate active sessions -> conflict status, seating blocked and logged for review.

## Dependencies and next work
Recover and verify the latest source/archive; inspect existing venue/table/reservation models, migration strategy, auth and CSRF before implementing. Add transactional constraints and tests first, then read-model/API and separate Tables tab. November 13 floor-plan editing and November 14 visual sizing must not alter physical inventory or active guest capacity. No public backend deployment until all security gates are independently verified.

## Sprint ledger
2026-11-12 08:00 Europe/Brussels: this document is the scoped Seat assignment/navigation contract, not an implementation. Pending: schema integration, endpoint, UI, concurrency/authorization/accessibility tests. Avoid repeating this specification in later hours; choose the next incomplete increment.
