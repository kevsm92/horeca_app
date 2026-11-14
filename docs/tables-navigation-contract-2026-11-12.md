# Tables navigation: seating read-model contract (2026-11-12, increment 08)

Status: **architecture contract only**, not integrated into an application. The repository's `develop` README explicitly says historical source archives have not been recovered. This document is a new, narrowly scoped contract; it does not claim a working Tables tab.

## Dedicated navigation
- Add a distinct top-level **Tables** tab (not a subsection of Reservations). Only authenticated venue staff with `tables:read` may view its content.
- List physical tables scoped to the authenticated venue; never trust a client-supplied venue ID. A table's stable physical ID, label, capacity, enabled flag and room are authoritative server-side.
- Status is **occupied** if exactly one active seating session exists for that physical table, **available** if enabled and none exists, and **unavailable** if disabled and none exists. More than one active session is a data-integrity error, never a display-only state.
- An occupied disabled table remains occupied until safely cleared; disabling must not silently evict guests.
- Floor-plan prototype may render static table positions with an accessible list alternative. Dragging, keyboard movement, coordinate persistence and revision checks are deferred to November 13.

## Seat action
- The Seat button must choose an existing physical table belonging to the actor's venue and a positive integer guest count not exceeding physical capacity. It must reject disabled or already occupied tables, and reject cross-venue identifiers.
- The server must authorize `tables:seat`, verify the reservation/session belongs to the same venue, and create the seating session atomically with a database-level uniqueness guard on active sessions per table. Recheck availability within the transaction; UI prechecks alone do not prevent double seating.
- Return an explicit conflict response for stale occupancy and let the user refresh; do not overwrite the existing session.
- All examples use synthetic data. No real customer details or live integrations.

## Verification criteria for future integration
1. Tables tab is separately navigable by keyboard and has visible available/occupied/unavailable labels independent of color.
2. An authorized venue A user can seat 1–capacity guests at a free venue A table.
3. Venue B cannot read or seat venue A tables; unknown/disabled/occupied tables and zero/over-capacity guest counts are rejected.
4. Two concurrent seat attempts at the same table yield exactly one active session and one conflict, verified against the actual database.
5. A static floor-plan and table list expose consistent statuses; status updates do not silently reassign seating.

## Dependencies and safety
Actual UI, persistence, auth/RBAC and concurrency tests are **blocked** until the current HORECA application source and its tests are recovered and verified. No deployment or public API is authorized by this specification. No chargeable services, real payments, customer communications or real data are used.

Next distinct increment: implement the dedicated Tables navigation route/component in the recovered app, with synthetic fixtures and accessibility tests; if still blocked, add a standalone floor-plan interaction prototype without pretending it is integrated.
