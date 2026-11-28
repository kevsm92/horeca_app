# Reservation availability reference contract — 2026-11-15

Scope: one offline, tenant-scoped table-availability predicate; **not** a booking endpoint, atomic reservation writer, or production release. The GitHub repository currently contains only its initialization README; prior ZIP implementations are not verified here.

## Input and decision
Inputs: venue_id, physical table_id, positive physical seat count, party_size, timezone-aware requested [start,end), immutable snapshot of bookings (venue_id, table_id, start, end, status), nonnegative turnover duration. Return available only if party_size is 1..seats, start < end, all relevant timestamps are aware, and no same-venue/same-table confirmed or seated booking overlaps. A cancelled booking does not block. For an existing booking [b_start,b_end), its occupied interval is [b_start,b_end+turnover). Compare instants rather than naive local wall time; preserve Europe/Brussels timezone metadata at boundaries. Unknown status and malformed relevant booking must fail closed pending validation.

## Required safeguards before accepting reservations
* Scope all reads and writes by authenticated venue_id; never accept tenant authority from a client-provided venue identifier.
* In one database transaction lock the physical table row (or use an equivalent exclusion/unique occupancy constraint), recheck availability, then insert. A pure predicate alone is vulnerable to concurrent double-booking.
* Enforce physical seats >= party size; do not infer capacity from floor-plan pixel dimensions. Do not allocate a table currently occupied by an active seating session.
* Modifications atomically exclude the reservation's own record and recheck conflicts. Cancellation must be idempotent, audited, and never silently free an occupied seating session.
* No customer notifications or external adapters are enabled. Synthetic fixtures only.

## Verified offline reference checks
A standalone Python standard-library reference implementation was executed locally with 7 unittest cases: capacity; overlap/adjacency; turnover; venue/table isolation; cancellation; invalid/naive windows; malformed existing booking fail-closed. Result: **7 passed**, 2026-11-15. That local reference code was not recovered from any historical archive and is not part of this GitHub documentation commit; these checks do **not** validate the repository application.

## Next increment
Persist an executable reference module and its regression tests in the verified repository structure, then add transactional locking and two-writer concurrency tests before wiring any API. No public backend or deployment authorized by this document.
