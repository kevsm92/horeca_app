# React Tables redesign → Python backend migration gate (2026-11-17 v0.1)

Status: architecture handoff only; **not an implemented integration**. Source reviewed: `prototypes/tables/2026-11-13-reference-redesign.html` on develop. React Vite manifest verified at `frontend/package.json`. The exact React Tables component and authenticated Python HTTP entry point must be located before implementation.

## Migration boundary

- Rebuild HTML layout as scoped React JSX + CSS (no iframe, inline DOM mutation, global IDs, `innerHTML`, or prototype script). Keep the responsive room, table/chair appearance, furniture inventory, tools, properties and revisions tabs.
- React state: `tables`, `placements`, `revision`, `selectedTableId`, `pendingPlacement`, `dragPreview`, `loadState`, `mutationState`. Use pointer capture and cleanup on cancel/unmount. Keyboard arrows (1%; Shift 0.25%), Escape cancels preview, and visible placement confirm/cancel buttons. Use ARIA labels/live status.
- The prototype hardcodes `VEN-001`/`VEN-002` and physical inventory and persists `horeca-layout-*` in localStorage. **Do not carry these into production authority**. Python derives venue from authenticated session and loads authoritative physical table IDs, seats, active occupancy, and saved placements from venue-scoped SQLite. Demo seeds only if explicitly marked fictional.
- Separate layout edits from seating. Removing a table from a *layout* must not delete the physical table or unseat guests. Seat action must validate physical capacity, active session and table conflict in one backend transaction. Visual size never silently changes physical seats.
- Keep existing table API client/tests if present; do not displace the separately prioritized food/drink catalog API integration. Do not publish the backend.

## Proposed contracts (confirm against existing routes before adding)

`GET /api/v1/floor-plan` → `{revision, tables:[{id,physical_seats,occupied_guests,status}], placements:[{table_id,x_percent,y_percent,width_cm,height_cm}], history:[{revision,action,created_at}]}`.

`PATCH /api/v1/floor-plan` with `{expected_revision, operations:[{type,table_id,...}]}` → new revision; reject stale revision with HTTP 409 and return no partial update. All table IDs must belong to the authenticated venue. Reject unknown IDs, duplicate placements, nonfinite/out-of-bounds coordinates, invalid dimensions, and operations that would violate occupancy/physical inventory. Apply transactionally; record immutable revision provenance.

`POST /api/v1/tables/{table_id}/seat` must be separate, authenticated, tenant-scoped and transactionally reject double seating and capacity overflows. The client must not supply a trusted venue ID.

## Acceptance checks

1. Render from authenticated Python synthetic data; loading, empty, forbidden and failed requests have explicit states.
2. Placement preview is unsaved until confirmed; cancel/Escape never writes; move via pointer and keyboard persists only on completion.
3. Stale revision returns 409; reload latest state without overwriting other editor; cancelled drag never commits.
4. Cross-venue table ID, forged venue parameter, unauthenticated request and unauthorized edit are denied; tests verify no state change.
5. Layout removal leaves physical inventory and active seating intact; seating conflict/capacity checks hold under concurrency.
6. Mobile/desktop, reduced motion, focus and keyboard navigation verified; no unsafe HTML injection.
7. Python tests, frontend tests and a local end-to-end read/edit/reload test pass before declaring integration complete.

## Delivery dependencies

Locate the current React Tables page, Python HTTP application/auth/session layer and SQLite table/floor-plan schema; verify develop head and concurrent frontend commits. Implement in subsequent bounded increments, with regression tests and explicit branch verification. No payment activation, external services, live data, hosting or spending.
