# Table resizing contract — 2026-11-14

Status: standalone architecture increment; the remote `develop` branch currently contains repository initialization, not recovered application source. No API integration or production deployment is claimed.

## Authority and invariants

A table belongs to one venue. Store `physical_seats` from verified inventory separately from `configured_seats` and visual `width_cm` / `depth_cm`. Visual resizing must never manufacture physical seating. Require `1 <= configured_seats <= physical_seats` and `active_guests <= configured_seats`. Active guests are derived from the authoritative active seating session, never from a client-supplied count. Example configurable editor dimensions: 40–500 cm on each axis; these are UI bounds, not legal or furniture standards.

## Atomic update contract

`PATCH /venues/{venue_id}/tables/{table_id}/layout` (future authenticated manager-only endpoint) takes `expected_revision`, integer `configured_seats`, integer `width_cm`, integer `depth_cm`. In one transaction, authorize venue membership, lock table and active seating session, compare revision, verify inventory and occupancy, update values and increment revision. Return 409 on stale revision or concurrent seating change, 403 on unauthorized tenant access, 422 on invalid dimensions or seat count. Never trust the path venue alone as authorization. The client should refetch on 409, preserving unsaved input for review.

## Regression cases

1. Six physical seats, four configured, three guests: reducing to three seats succeeds; two fails.
2. Request seven seats for a six-seat table fails regardless of visual dimensions.
3. Increasing width to 500 cm leaves seat count unchanged.
4. Revision mismatch fails without mutation.
5. Cross-venue requests fail without disclosing table state.
6. Concurrent seating and resize serialize on the same table/session lock; if occupancy rises beyond proposed seats, resize fails.
7. Non-integer values (including booleans), corrupt existing inventory and out-of-range dimensions fail.
8. Keyboard-operable numeric fields expose labels, errors and updated dimensions; drag coordinates remain a separate concern.

## Implementation dependency

Recover and verify actual application code, persistence schema, authorization and existing table workflows before wiring this contract. Do not claim a database lock or API security from this specification alone. The independent reference validator was exercised locally with nine Python unittest cases passing, but it is not included in this specification commit; integration tests remain pending. Synthetic-only, €0 spending, no external services, no deployment.
