# Reservation modification and cancellation contract v0.1 — 2026-11-15

Status: **architecture-only**, separate from the previously completed availability evaluator contract. No verified application source is present in the inspected repository README and reservation specification. This document does not claim implementation or passing application tests.

## Scope
Transactional **modify** and **cancel** of an existing venue-owned reservation, without guest communications, payments, or external systems. Do not implement a public API from this contract alone.

## Authorization and identity
- Authenticate actor; resolve authorized venue membership and permission `reservation:modify` or `reservation:cancel` server-side. Lookup must be scoped by `(venue_id, reservation_id)`, returning the same non-disclosing 404 for absent and cross-venue IDs.
- Client submits `expected_revision` and `Idempotency-Key`; key is scoped to venue, actor, operation, and canonical request digest. Reusing a key with different payload must fail with 409, not replay a different result.
- Guest identity, contact details and payment state are out of scope; use synthetic IDs only.

## State transitions
| Current | Modify | Cancel |
| --- | --- | --- |
| pending | allowed after full rule/capacity check | allowed |
| confirmed | allowed after full rule/capacity check | allowed |
| seated | **denied**: use explicit seating workflow | **denied** while session active |
| completed | denied | denied |
| cancelled | denied | idempotent only for exact previously completed request |
| no_show | denied | denied |

Status vocabulary must be reconciled with recovered source before migration. Cancellation is a terminal tombstone; never delete its audit trail. Cancellation must not silently close an active seating session.

## Atomic modification
1. Start DB transaction; authorize venue, lock reservation row and allocation scope in stable order; verify current revision and mutable state.
2. Validate new start, duration, party size and table assignment against venue rules, actual physical seat capacity, opening windows, DST resolution and turnover. Exclude **only this same reservation** from conflict evaluation; no cross-venue exclusions.
3. Recheck overlaps against blocking reservations and active seating sessions under transaction isolation. The old allocation stays intact until the new one is valid; if any check fails, rollback unchanged.
4. Update reservation and protected interval together, increment revision once, append immutable audit event with actor, UTC timestamp, old/new field values and reason code; store idempotent outcome atomically.
5. Return new revision and allocation. On stale revision or conflicting table, return 409 with no partial update. Database exclusion/serialization strategy from availability contract remains mandatory.

## Atomic cancellation
1. Lock and authorize scoped reservation; verify revision, status, and no active seating session.
2. Set status cancelled, increment revision, retain old table and interval as historical data but exclude cancellation from *future* availability blocking; append actor/reason/time audit event and idempotency outcome in the same transaction.
3. Repeated **same key + same digest** returns the original outcome. New cancellation attempt on terminal state must not fabricate another event.
4. Do not notify guests or issue refunds; any later notification/payment integration requires separate authorization and mock-first design.

## Concrete synthetic acceptance cases
| Case | Expected |
| --- | --- |
| Confirmed R1 rev=4 moves T1→T2, T2 free and capacity sufficient | Commit rev=5; exactly one modification audit event |
| T2 overlaps another confirmed booking by one minute | 409; R1 remains on T1 rev=4 |
| New party size 5 on physical capacity 4 | Reject; unchanged |
| Cross-venue R1 ID queried by actor in venue B | Non-disclosing 404; no read/update |
| Two concurrent updates both expect rev=4 | Exactly one commit; other 409 |
| Client retry with same idempotency key and digest | Same result; no second audit event |
| Same key with different payload | 409; unchanged |
| Cancel confirmed R1 rev=4 with no active seating | Commit cancelled rev=5; one audit event |
| Cancel seated R1 with active seating session | Reject; session remains open |
| Cancel already cancelled with a new key | Reject; no second event |
| Local time in Europe/Brussels DST gap or ambiguous overlap | Reject until resolved explicitly; no mutation |
| Cancellation transaction fails before audit/outcome persistence | Entire transaction rolls back; booking still blocking |

## Implementation dependencies and gates
Recover application source; reconcile existing status names; choose DB-specific locking/exclusion guarantees; implement authenticated venue RBAC, CSRF/origin protection, transactional idempotency and real concurrent database tests. Validate all 12 synthetic cases, audit immutability, rollback and negative isolation before enabling writes. Keep `main` unchanged until reviewed integration.

**Cost/safety:** €0 additional spending. No deployment, real customer data, communications, payment processing, metered infrastructure or supplier actions. No compliance certification implied.
