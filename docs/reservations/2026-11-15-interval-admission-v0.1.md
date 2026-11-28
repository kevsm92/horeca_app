# Reservation interval conflict contract v0.1 — 2026-11-15

Status: **design-only, not wired to an application**. Source recovery is pending: the verified `develop` README states historical application archives are absent. This is one bounded advanced-reservations increment: deterministic, venue-scoped table interval admission. No live bookings or guest communications.

## Inputs and trust boundaries

An authenticated venue operator requests `create_hold(venue_id, table_id, party_size, starts_at, service_minutes, turnover_minutes, request_key)`. The server derives `venue_id` from authorization context, never trusts a client-supplied tenant identifier. All timestamps are timezone-aware instants stored as UTC; venue timezone is used only for display and local booking-policy evaluation. Durations are positive integers, turnover nonnegative, and start/end arithmetic must reject overflow. `request_key` is unique per venue and operation and bound to a canonical request hash. Physical table ownership, enabled status and capacity come from authoritative inventory; `party_size >= 1` and `party_size <= table.physical_seats`. A visual floor-plan dimension never changes capacity.

## Admission algorithm (transactional)

1. Authorize booking write access for venue V; load table T with `T.venue_id = V`. A missing or foreign table produces the same not-found response. Validate configured booking horizon, party size and durations.
2. Within a database transaction, resolve `(V, request_key)`: matching request hash returns the prior outcome; different hash returns conflict. Lock the target table row (or equivalent serializable per-table advisory lock) **before** overlap checking. All writers, including edits, must use the same locking protocol.
3. Define half-open protected interval `[start, start + service_minutes + turnover_minutes)`. Check all active holds/confirmed reservations for the same `(V,T)` using `existing.start < requested.end AND requested.start < existing.protected_end`. Cancelled/expired holds do not block. A modification excludes its own reservation ID but checks every other active record.
4. On no conflict, insert the hold and idempotency outcome atomically, then commit. On conflict, persist a stable rejected outcome for that idempotency key and return `409 table_unavailable`. Roll back on transient database errors and permit a safe retry.
5. Confirm a hold only if still active and not expired, under the same table lock; revalidate policy and occupancy. Cancellation records actor/time/reason without deleting provenance. Never silently replace a confirmed reservation.

A database-enforced exclusion constraint on `(venue_id, table_id, protected_interval)` for active rows is preferred when supported; otherwise the lock and serializable transaction are mandatory. Cross-table reassignment locks both table IDs in stable sorted order to avoid deadlock.

## Executable acceptance examples (for future implementation)

| Case | Existing protected interval UTC | Requested interval UTC | Expected |
|---|---|---|---|
| Overlap | 18:00–20:15 | 20:00–21:00 | 409 |
| Adjacent | 18:00–20:15 | 20:15–21:00 | accepted |
| Same key, same payload | 18:00–20:15 (own request) | identical replay | same original result, no second row |
| Same key, different payload | original payload | changed time | 409 idempotency conflict |
| Foreign venue table | table owned by B | actor from A | 404, no disclosure |
| Capacity exceeded | 4 physical seats | party of 5 | 422, no insert |
| Two concurrent requests | empty table | identical overlapping windows | exactly one accepted |
| Cancelled record | 18:00–20:15 cancelled | 18:30–19:30 | accepted if no other blocker |
| Modified reservation | existing R at 18:00 | move R to 19:00 | ignore R itself; reject on any other active conflict |
| DST transition | Brussels local ambiguous time | no explicit offset | reject ambiguous local input; require offset or UTC |

## Pending implementation gates

Recover actual source and migrations, choose the real database dialect, implement transactional locking plus database constraints, and execute concurrency/tenant/capacity/idempotency regression tests. No test outcome is claimed here. The specification is not evidence of a secure API or a deployed reservation feature. No external calls, paid services or production data are authorized.

Next distinct reservation increment: booking modification and cancellation state-machine invariants, after checking the latest `develop` head to avoid duplication.
