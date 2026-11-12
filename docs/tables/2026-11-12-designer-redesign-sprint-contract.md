# HORECA floor-plan designer — UX redesign and dated sprint acceptance contract
Date: 2026-11-12 (Europe/Brussels)
Status: DESIGN SPECIFICATION ONLY — this file does not mean the functionality is implemented.
Repo baseline inspected: `develop` at `26a1aeb406d73e21cbd4c17f07c5927b086e7589` (fixed four-table HTML prototype); `main` at `46115441ddb73212178a6d24f5e5cf832485b3e7`.

## Why redesign
The 12 Nov prototype has a separate Tables tab, occupancy colours and fixed-position buttons, but no designer mode, venue-template onboarding, drag, rotation, persistence, physical-inventory-connected placement or responsive editing surface. Do NOT replace its Seat safety contract with visual-only assumptions.

## Target information architecture
- Keep a **Tables / Live service** tab for occupancy, reservations and Seat-to-table actions. Workers should not accidentally edit a floor plan while serving.
- Add **Design layout** as an explicit authorized mode inside Tables. Draft edits never change live seating, orders, physical inventory or capacity.
- Full-width editor: top bar for venue, room, Design/Service toggle, draft/publish state, undo/redo and save; **left panel** for blank/template choice and eligible physical table inventory; **centre canvas** for floor geometry and interactive objects; **right inspector** for selected table's identity, real capacity, position, angle and numeric dimensions; footer for validation and keyboard instructions. Collapse panels on mobile.
- Clear statuses: available, occupied, reserved, blocked/out of service, unplaced physical tables, unsaved draft, publish conflict. Statuses come from authoritative service data, not floor drawing or arbitrary colours.

## Start a new design — two paths
1. **Blank canvas**: start with an empty named room, configurable dimensions/scale, accessible grid and a visible empty-state instruction. No fictional tables appear by default.
2. **Venue layout starter**: café, seated restaurant, bar/pub, terrace, banquet/event room, and hotel dining. Starter templates are OPTIONAL sample walls/zones/paths/placement guides, NOT physical table creation or proof of venue geometry. Managers can edit or reject template suggestions.
3. A real physical table may be placed only by choosing a **venue-owned inventory record** with an available table ID. Templates may show unbound ghost placeholders, which must not be treated as seatable or counted toward capacity until bound.
4. Multiple rooms are an extensible model; initially one room in the prototype. Switching venue/room never silently merges assets or seated sessions.

## Physical inventory gate (hard rule, not visual assumption)
- Every table on an active floor plan refers to exactly one `physical_table(venue_id, table_id)` record; a physical table cannot be placed twice in one venue's current layout.
- Left panel explicitly shows `N placed / M physical tables`, remaining unplaced tables, assigned capacity and active guests. No "add table" from an unlimited drawing library.
- Table and seat inventory are distinct from dimensions and drawn chair icons. Visual resize/rotation NEVER creates extra physical tables or seats. Adding/removing actual seats requires an authorized inventory adjustment and cannot reduce capacity below currently seated guests.
- Venue IDs and permissions must be derived/validated by authenticated backend; client-supplied inventory is illustrative only. Publish revalidates inventory, occupancy, room binding and revision server-side.
- Drawing walls, doors, bars, counters and inaccessible zones is allowed from a separate non-seating objects palette; it does not create seatable capacity.

## Editor interactions to build incrementally
- Pointer drag (mouse, touch, pen) for tables and non-seating furniture, with snap-to-grid, alignment guides, collision/walkway warnings and edge clamping; a drag must not change table identity.
- Rotation of selected table via clearly labelled rotate handle and numeric angle field (0–359°); support 15° step buttons, keyboard rotation and free numeric adjustment. Angle is **visual geometry**, not seating capacity. Avoid treating CSS-only rotation as a saved model.
- Accessible fallback: focusable canvas object; arrow keys nudge position, Shift+arrows larger nudge, labelled rotate clockwise/counter-clockwise buttons, inspector numeric X/Y/rotation. Accessible selection announcement and visible focus.
- Numeric visual width/height and shape choices (square/round/rectangle) stay separate from authoritative seat capacity. Do not allow an edit that creates a duplicate table, overlaps restricted room bounds, or silently removes an occupied table.
- Undo/redo within draft; save draft with optimistic revision/ETag and explicit conflict resolution. Publishing a layout change affecting an actively seated table requires a separate safe workflow; for the first implementation **reject publishing such a change** until sessions are closed or an authorized future transition is designed.
- Auto-arrange may only propose placements for existing unplaced physical tables, with preview and user confirmation; never change inventory or live seating automatically.

## Minimal model proposal (not yet migrated)
`floor_plan(venue_id, room_id, draft_id, revision, status, width_mm, height_mm, base_template)`
`plan_object(object_id, venue_id, room_id, draft_id, kind, physical_table_id|null, x_mm, y_mm, width_mm, height_mm, rotation_deg, shape)`
Binding `physical_table_id` is required iff object `kind=physical_table`, unique per published plan; references must be venue-scoped. Positions and rotations are bounded, versioned layout data. Use integer millimetres/degrees in domain records; pixels only for rendering. A plan record does not change inventory capacity. Multi-room moving requires distinct authorized workflow.

## Date-aligned implementation and acceptance
- **Nov 12 — Designer shell, new design direction:** separate Service vs Design surface; blank/venue-template selection; read-only inventory palette and placed/unplaced counts; initial synthetic fixture. Test empty canvas and template does not invent physical tables.
- **Nov 13 — Spatial edit slice:** pointer drag, keyboard movement, rotate handle + numeric angle, grid snap and saved coordinates with revision checks. Test mouse, keyboard, touch fallback, angle normalization and conflict.
- **Nov 14 — Table geometry and seats:** numeric dimensions and shapes, physical inventory placement binding, seat adjustments that never exceed real available inventory or undercut active guests. Test duplicate binding, mismatched venue, occupied shrink and no seats from resize.
- **Nov 15 — Table detail read model:** operational mode shows active session, orders, item quantities, guests and integer-cent totals only from verified sources; planner does not fabricate totals.
- **Nov 16 — Hardening:** concurrent edits, double seating, room collisions, accessible keyboard paths, stale publish conflicts, permissions/tenant tests.
- **Mar–Apr 2027 — Depth:** multi-room editing, joins/splits, versioned history, undo/redo across drafts, template management and publish review. Bring forward narrow dependencies if needed; do not drop other dated commitments.

## Acceptance cases for future implementation
1. Blank starts at 0 placed; venue template displays guidance but cannot increase physical inventory.
2. Place physical table T1 once; duplicate T1 placement rejected, even across current-plan rooms; T1 from venue B rejected.
3. Add graphical chairs or resize/rotate T1: physical seat count unchanged.
4. Rotate T1 90°, save, reload: exact angle and coordinates restored; keyboard and pointer operations agree.
5. Change layout on stale revision: conflict; no silent overwrite.
6. An occupied table cannot be deleted, rebound, or published in an unsafe changed layout; closing a session preserves seating history.
7. Authoritative service rejects overcapacity/double-seat regardless of what floor plan displays.
8. Read-only staff can view operations but cannot enter/publish designer; keyboard/screen reader alternatives exist.

## Current limitations and safeguards
As of this document, only the original fixed-position HTML prototype and database reference work have been verified in the repository. Application source, authenticated API, live inventory and deployment are not verified. All fixtures must remain synthetic. No paid/metered services, production data, customer communications, live payment providers or public backend; €0 additional cost. No changes to main as part of this sprint.
