# 2026-11-14 — Table visual dimensions versus physical seats (architecture increment 01)

Status: **standalone design only**. The reachable `develop` README explicitly states that historical application sources have not been recovered. No API, UI, migration, or integrated regression test is claimed.

## Boundary and data contract

A physical table belongs to exactly one venue and has an immutable inventory identity. Its **authorized seat inventory** is not inferred from floor-plan pixel dimensions.

```text
physical_table(
  venue_id UUID NOT NULL,
  table_id UUID NOT NULL,
  inventory_seat_limit INTEGER NOT NULL CHECK (inventory_seat_limit BETWEEN 1 AND 50),
  configured_seats INTEGER NOT NULL CHECK (configured_seats BETWEEN 1 AND 50),
  visual_width_cm INTEGER NOT NULL CHECK (visual_width_cm BETWEEN 40 AND 600),
  visual_depth_cm INTEGER NOT NULL CHECK (visual_depth_cm BETWEEN 40 AND 600),
  revision BIGINT NOT NULL DEFAULT 0,
  PRIMARY KEY (venue_id, table_id),
  CHECK (configured_seats <= inventory_seat_limit)
)
```

The numeric centimeter bounds are **prototype UI validation limits**, not legal or ergonomic minimums; venue policy and actual furniture must be reviewed before use. Inventory limit must originate from a verified venue-owned physical inventory record, never from a request parameter. Do not use width/depth to calculate or silently change seating capacity.

## Mutation contract

`PATCH /venues/{venue_id}/tables/{table_id}/configuration` requires authenticated venue-scoped manager permission, CSRF protection for cookie sessions, and `If-Match` with the table's revision. Body may contain integer `visual_width_cm`, `visual_depth_cm`, and/or `configured_seats`; reject unknown fields, booleans, floats, negatives, missing revision, or empty changes. No implicit defaults for omitted fields.

Execute a **single database transaction**: lock the venue-owned physical-table row; load the trusted inventory seat limit; count guests in active seating sessions for this exact venue/table under the same serialization discipline as seat/unseat operations; validate `active_guest_count <= proposed_configured_seats <= inventory_seat_limit`; validate width/depth independently; compare revision; atomically update changed values and increment revision. Return new revision and actual values. Use 404 for wrong-venue or nonexistent table (avoid existence leaks), 409 for stale revision or active occupancy conflict, 422 for invalid dimensions/seats. Repeated PATCH with a stale revision must not apply again. Seat assignment must lock/serialize against the same table row and reject oversubscription and double seating.

**Concurrency prerequisite:** row locking alone does not prevent races unless every seating writer uses the same locking protocol; add database-level uniqueness for active seating assignment and transaction tests before enabling this route. If capacity changes and seat assignment race, one transaction must fail safely.

## UI contract

In the distinct Tables tab, provide numeric controls labeled “Visual width (cm)”, “Visual depth (cm)”, and “Available physical seats”. Show “Inventory maximum: N” and “Currently seated: M”; disable Save for proposed seats below M or above N, but always enforce on the server. Keep draggable floor-plan coordinates independent from size and seat count. Keyboard-only controls must expose focus, arrow-key movement and accessible announcements; changing visual size must not reposition the table unexpectedly. Refresh on 409 and show a non-destructive conflict message.

## Synthetic acceptance matrix

1. Inventory 6, occupied 4: resize 100×80 to 120×90 without changing seats -> accept.
2. Inventory 6, occupied 4: configured seats 4 -> accept; seats 3 -> 409.
3. Inventory 6, occupied 0: seats 7 -> 422; seats 6 -> accept.
4. Width 0, depth 601, seat count 2.5, booleans or unknown keys -> 422; no partial writes.
5. Wrong venue/table -> 404, without revealing the table.
6. Concurrent resize and seat assignment -> serial outcome, never occupancy greater than configured seats.
7. Same revision used by two edits -> exactly one succeeds; other 409.
8. Visual dimensions changed -> inventory_seat_limit, configured_seats, table position and active sessions remain unchanged.
9. Accessible keyboard input, labels, error association and focus restoration -> manual/automated UI checks when source is available.

## Follow-up dependencies

Recover and verify the actual application source and test harness; inspect existing table/session schemas; implement an additive migration and the transactional service; run database concurrency, tenant-isolation, CSRF, UI accessibility and regression tests before considering any deployment. This file is a dated completed **architecture** increment, not evidence of implemented behavior. No payments, external communications, camera capture, production data, or hosting are involved.
