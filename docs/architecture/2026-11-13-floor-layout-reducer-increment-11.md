# Floor-plan pure revision reducer — 2026-11-13, increment 11

Status: **offline prototype validated locally; not integrated into the application**. This increment is distinct from the existing optimistic-locking contract in `docs/architecture/2026-11-13-floor-layout-revisions.md`: it exercises the proposed *pure command reducer* for atomic floor-position validation.

## Reducer interface

`move_tables(layout: FloorLayout, expected_revision: int, moves: tuple[tuple[table_id, x_mm, y_mm], ...]) -> FloorLayout`

Immutable inputs: `FloorLayout(floor_id, venue_id, width_mm, height_mm, revision, tables)`; each `TablePosition(table_id, x_mm, y_mm, width_mm, height_mm)`.

Checks, in order: expected revision is a nonnegative strict integer; revision matches; batch contains 1–50 moves; positive integer floor bounds; unique stored table IDs; each move has exactly three fields; table exists on the given floor; no duplicate move IDs; coordinates and persisted visual dimensions are strict integers (reject bool and float); coordinates nonnegative; positive table footprint fits floor bounds. On success return a **new** layout with exactly one revision increment, updated positions in original order, and untouched other tables. Any error leaves the original unchanged. Seat counts and occupancy are not modified. Collision detection is deliberately excluded pending venue-specific policy.

## Verified synthetic tests (local Python 3 unittest)

Executed `python -m unittest -v test_floor_layout_revision.py`: **5 tests, all passed**. Covered valid move and immutability; stale revision replay; invalid/partial batches including cross-floor ID, duplicates, negative and out-of-bounds coordinates, booleans/floats, 51 moves; malformed revision types; two-table batch with one revision increment. The standalone source/test files are available as run attachments, but **not claimed to be merged into the repository** by this documentation commit.

## Integration gates

This reducer is not an authorization boundary or concurrency primitive. Actual persistence requires venue/floor RBAC and CSRF enforcement, database transaction with compare-and-swap/row lock, server-side table ownership validation, audit event, and regression tests for concurrent writers. The source-of-truth application is not recovered from historical archives. Drag and keyboard UI remain separate future increments. No production deployment, real data, paid services, or external communications.
