# Weekly roster snapshot contract — 2026-11-27 (15:00 Europe/Brussels)

Scope: backend-only, manager-authorized weekly roster **read** prerequisite for issue #4. A standalone offline Python prototype was tested separately; this document does not assert integration with existing backend or authenticated routes.

## Contract (proposed GET /api/v1/manager/roster?week=YYYY-MM-DD)

- Server resolves venue_id and manager grant from authenticated session; never trust client-supplied venue_id.
- Require ISO Monday in venue-local calendar. Respond with week_start, exclusive week_end, venue timezone, provenance and per-person scheduled shifts (stable staff/shift IDs, role, station, timezone-aware start/end).
- Each shift is `scheduled`; attendance remains `unknown` unless an independent authorized kiosk clock-in event exists. Never infer actual presence from roster.
- Include explicit unavailable/empty/error statuses; do not emit fictional shifts as live records.
- Filter staff and shifts by venue before joining. Reject dangling cross-venue staff references and duplicate IDs. Detect overlapping same-person shifts, including cross-midnight, in authoritative write transactions.
- Manager-only read, least-privilege display fields, no HR diagnosis, earnings, personal contact data or performance scoring. Audit access with venue and actor IDs.
- Future writes require expected revision, atomic compare-and-swap, overlap/conflict checks, manager grant and append-only audit. No external notifications.

## Verified standalone prototype

A local `roster_snapshot.py` domain prototype was executed with `python roster_snapshot.py -v`: **4 tests passed** (venue isolation and cross-midnight, cross-venue reference rejection, overlap rejection, invalid/naive timestamp rejection); `python -m py_compile` succeeded. This repository document is **not** a claim that those tests ran against GitHub's backend source. Source integration and exact route selection remain pending inspection of existing backend modules.

## Next dependency

Locate authoritative Python staff/shift schema and session/RBAC middleware on develop, then integrate a read-only route with focused HTTP tests for 401/403, cross-venue isolation, empty week and schedule-vs-attendance provenance. Do not deploy.
