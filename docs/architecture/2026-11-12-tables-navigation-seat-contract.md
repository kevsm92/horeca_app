# Tables navigation and seating contract — 2026-11-12, increment 01

Status: **architecture specification only**. The verified `develop` README states historical application archives have not been recovered; no working UI, API or database was available to test. This document is not an implementation or evidence of deployment.

## Scope
Introduce a distinct **Tables** navigation destination and define the smallest safe Seat-to-table flow. The Tables destination shows venue-filtered physical tables and their current occupancy; the Reservations **Seat** action must never mark a party seated without an actual, valid physical table assignment. This increment deliberately excludes drag editing (Nov 13), dimensions (Nov 14), order totals (Nov 15), and concurrency implementation (Nov 16).

## Navigation and state
- Primary navigation: `Reservations` and `Tables` are separate, keyboard-accessible destinations with clear active-route semantics and visible focus indicators.
- Tables view: accessible list is canonical; an optional schematic floor-plan is only a secondary view and must not imply measured geometry.
- Each table belongs to exactly one venue and has an immutable physical-table identifier, label, positive physical capacity and active/inactive flag.
- Display status: `available` (no active seating), `occupied` (one active seating), `unavailable` (inactive or administratively blocked). Do not infer status from reservation timestamps alone. Counts display `seated_guests / physical_capacity` for occupied tables.
- An active seating session has `venue_id`, `table_id`, `reservation_id` (optional for walk-ins), `guest_count`, `started_at` (timezone-aware), `ended_at` (null until closed) and actor audit metadata. Never expose one venue's tables or sessions in another venue.

## Seat command contract
Input: authenticated actor/venue context, reservation ID, table ID, expected reservation revision, idempotency key. Server resolves the venue from trusted actor scope, not client-supplied identifiers.

In a single database transaction: authorize venue and seating permission; verify reservation is seatable, table active and same venue, `guest_count > 0` and `guest_count <= physical_capacity`; verify no active seating for that table or reservation; create session; update reservation status and revision; append audit event; commit. A unique active-session constraint for each `(venue_id, table_id)` and each seated reservation must enforce exclusivity independently of UI checks. Use conditional updates/locking appropriate to the actual database. Same idempotency key and identical request returns the recorded outcome; same key with different payload fails. On conflict, return an actionable `409` and refresh table statuses. On authorization failure return `403` or masked `404`; never leak cross-venue data. No partial reservation-status update is allowed.

UI: Seat opens a table selector filtered to available, active, sufficient-capacity tables. Display table label/capacity and allow cancellation. Confirm only after the server commits. Pending/error states are announced to assistive technology; selection and confirmation must work without a mouse.

## Acceptance scenarios (synthetic, to implement after source recovery)
1. Venue A reservation for 3 guests seats at A-04 capacity 4; Tables view shows `occupied 3/4` and reservation points to the same active session.
2. A table with capacity 2 is rejected for 3 guests; no session or reservation-status change.
3. Venue B table ID cannot be assigned by venue A actor; no cross-venue details leak.
4. Two simultaneous Seat requests for the same physical table: exactly one succeeds; the other conflicts.
5. Repeated identical idempotency key does not create a second session; mismatched replay fails.
6. An inactive/blocked table, already seated reservation, stale revision, and zero guest count each fail atomically.
7. Tables tab, table selector and confirmation are keyboard accessible; status is readable without relying on color.
8. Closing a seating session frees the table only after an authorized, audited close operation.

## Delivery and dependency gates
- Recover and inspect historical source/archive and prior hourly artifacts before implementing; this repository currently contains only the initialization README as verified in this run.
- Confirm actual framework, schema, migrations, tenant authorization, auth/session protections and existing reservation flows. Write schema constraints and API tests before connecting UI.
- Keep all fixtures fictional and payment integrations offline. No hosting, public API, supplier/customer communication or charges.
- Next scoped increment: implement venue-filtered read-only Tables navigation against the recovered codebase, then Seat command transaction and negative tests; defer floor-plan drag/resize to their assigned dates.
