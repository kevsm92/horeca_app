# Floor-plan coordinate persistence and optimistic revision contract (2026-11-13)

Status: **standalone design**, not integrated or tested against HORECA application code. The accessible `develop` README says historical application sources have not been recovered. This milestone defines the smallest safe server contract for saving table positions; dragging and keyboard UI are follow-ups.

## Scope and invariants

- Venue-owned physical table `table_id` and venue-owned `floor_id` are immutable identifiers; a table can appear at most once in its assigned floor. The authenticated actor must have `floorplan:edit` for the venue. Never trust venue membership from a request body.
- Store integer `x_mm` and `y_mm` relative to the floor origin (not browser pixels), both nonnegative. Each floor defines positive `width_mm` and `height_mm`. Visual dimensions and physical seat inventory are separate; moving a table does not alter seats, occupancy or seating sessions.
- A `layout_revision` is a monotonic integer scoped to the floor. Every successful mutation increments it exactly once. All moves require an expected revision and are atomic with revision comparison. Rejected writes must leave all positions and revision unchanged.
- Require all table footprints to fit within floor bounds using persisted visual width/height; reject overlap only if the venue has explicitly enabled a no-overlap layout rule. Do not silently clamp coordinates or move other tables.
- The server is authoritative for saved positions. The client may preview drag movement but must display saved state only after success; on conflict reload latest layout, announce the conflict, and offer an explicit retry.
- Accessibility: focusable table control, Arrow keys move by a configured grid step, Shift+Arrow moves by a larger documented step, Escape cancels preview, Enter/Space commits, and an aria-live status announces table name, coordinates and save/conflict result. Pointer dragging must use the same save endpoint.
- No public endpoint before authentication, authorization, tenant isolation, CSRF and relevant security tests pass.

## API proposal

`GET /venues/{venue_id}/floors/{floor_id}/layout` returns `{floor_id,layout_revision,bounds_mm:{width,height},tables:[{table_id,x_mm,y_mm,width_mm,height_mm}]}`.

`PATCH /venues/{venue_id}/floors/{floor_id}/layout/positions` accepts:

```json
{"expected_revision":7,"moves":[{"table_id":"table-A","x_mm":1200,"y_mm":850}]}
```

All coordinates are integers; no float/NaN, duplicate IDs, unknown/cross-venue IDs, or empty moves. Maximum 50 moves per request. Respond `200` with updated revision and canonical positions; `409` for stale revision; `400/422` for invalid geometry; `403` for unauthorized actor; `404` for inaccessible floor/table without disclosing other venues. A repeated request with an old revision returns `409`, never applies twice. A later idempotency key can improve lost-response recovery.

## Transaction sketch (SQL-neutral)

1. Authenticate session, enforce CSRF for browser mutation and authorize venue/floor edit.
2. Start transaction; lock the venue-owned floor layout row.
3. Check `expected_revision == layout_revision`; otherwise rollback and return `409`.
4. Verify every moved table belongs to this floor and venue; validate bounds against persisted footprint and any enabled collision policy.
5. Update only requested positions; increment floor revision once; append audit event with actor, floor, prior/new revision, before/after coordinates and server timestamp.
6. Commit. On any exception rollback all changes. Return canonical saved coordinates.

## Synthetic acceptance cases (future executable regression tests)

| Case | Initial revision | Request | Expected |
| --- | ---: | --- | --- |
| Valid move | 7 | table-A to (1200,850), expected 7 | 200, revision 8, persisted |
| Concurrent editors | 7 | two writes both expected 7 | exactly one 200; other 409 |
| Cross-venue table | 7 | foreign table ID | 404, no mutation |
| Out of bounds | 7 | negative x or footprint exceeds width | 422, no mutation |
| Partial batch failure | 7 | valid A and invalid B | reject entire batch, revision 7 |
| Duplicate table IDs | 7 | A listed twice | 422, no mutation |
| Keyboard vs drag | 7 | same resulting coordinates | same server validation and audit |
| Seat invariant | 7 | valid move of occupied table | seating session and physical capacity unchanged |
| Revision replay | 8 | repeat request with expected 7 | 409, no second move |
| Unauthenticated | 7 | any mutation | 401, no mutation |

## Dependencies / next work

Recover and inspect actual HORECA source and migrations before integrating this contract. Implement floor-scoped schema and transactional revision check first, then browser drag/keyboard controls and regression tests. No deployment or live data. This design makes no claim that these behaviors already exist.
