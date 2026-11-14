# 2026-11-12 — Tables designer shell: structural safety baseline (increment 04)

Scope: independently inspect the current `prototypes/tables/2026-11-12-designer-shell.html` on `develop` before adding interactive editing. This is a *static source inspection*, not a browser or backend test.

## Verified against source blob `7242259835f1b004da7b821e53db7d6d42bf6db7`

Seven independent source assertions passed (7/7):
1. Blank draft initializes with no placed tables.
2. Placement checks whether the table is already placed.
3. Separate Service and Design tab controls exist.
4. No fetch/XHR/WebSocket/HTTP URL occurs in this standalone HTML source.
5. UI distinguishes physical seat capacity from visual dimensions.
6. Mode notice explicitly says there is no backend persistence.
7. Placement function rejects unknown physical IDs and duplicate IDs.

## Critical gaps / next work

- Static assertions cannot prove keyboard operation, mobile pointer dragging, screen-reader semantics, occupancy synchronization, backend venue ownership, or resistance to malicious requests.
- Service tab is only a reference shell; do not interpret it as an integrated Seat-to-table workflow.
- Next distinct Nov 12 increment: validate and implement a venue-scoped Seat-to-table navigation flow against verified seating commands, with negative tests for wrong venue, occupied table and insufficient capacity.
- Nov 13+ editor: move/rotate controls, keyboard equivalents, revision-safe persistence and bounds checks; preserve immutable physical table IDs and do not infer seat inventory from drawings.
- Future optional isometric 3D preview must consume the same verified 2D geometry and be browser-only, lazy-loaded and disableable; no 3D implementation is claimed here.

No live service, personal data, payment, deployment, external calls, or cost. This audit does not constitute an application security certification.
