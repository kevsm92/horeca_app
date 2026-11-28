# KDS ticket lifecycle contract v0.1 — 2026-11-26

Status: **standalone architecture contract**, not integrated or deployed. The initial README is stale: inspection after this commit confirmed existing offline modules `backend/kitchen_ticket.py`, `backend/kitchen_ticket_intake.py` and `backend/kitchen_reconciliation.py` on `develop`. This contract is a gap/target design, not a description of implemented behavior. This increment defines one bounded feature: a venue-scoped, monotonic kitchen/bar ticket lifecycle. No real orders, guests, workers, or integrations.

## Domain and ownership

`kds_ticket(id UUID, venue_id UUID, source_order_id UUID, source_order_revision INTEGER, station TEXT, state TEXT, created_at_utc TEXT, updated_at_utc TEXT, version INTEGER)`.

`station` is one of `kitchen`, `bar`. `state` is one of `queued`, `preparing`, `ready`, `served`, `cancelled`. A ticket belongs to exactly one server-derived venue. A single source order may create separate station tickets. Require unique `(venue_id, source_order_id, source_order_revision, station)`; do not accept venue ID from browser input. The order domain remains the source of truth for item quantities and amendments.

## Transition contract

| From | Allowed to | Actor |
| --- | --- | --- |
| queued | preparing, cancelled | authorized station operator / manager |
| preparing | ready, cancelled | authorized station operator / manager |
| ready | served | authorized server / manager |
| ready | cancelled | manager only, reason mandatory |
| served | none | terminal |
| cancelled | none | terminal |

No implicit reopening or state rewinding. A replacement ticket for an amended/voided order uses a new source revision, linked to the original; never rewrite the prior ticket history. All transitions require expected `version` and execute atomically: `UPDATE ... WHERE id=? AND venue_id=? AND state=? AND version=?`, incrementing version exactly once; zero affected rows is a conflict or not-found, not success. Duplicate command IDs scoped to venue and ticket return the original result only when payload digest matches; conflicting replay is rejected.

## Immutable event trail

`kds_ticket_event(event_id, venue_id, ticket_id, command_id, from_state, to_state, actor_id, reason, occurred_at_utc, source_order_revision)` is append-only. A transition and its event/outbox row are committed in the same SQLite transaction (`BEGIN IMMEDIATE`). No fabricated event timestamp from a client. Cancelled tickets remain visible in history, and audit events are not deleted when a display clears.

## Views and missing-ticket reconciliation

Kitchen and bar views filter by the **authenticated** principal's venue and authorized station; managers can view both. Show queued/preparing/ready with age computed from UTC timestamps, not worker-performance scores. Reconciliation compares eligible accepted order revisions to their expected station ticket keys and reports `missing`, `unexpected`, or `revision_mismatch` without automatically creating, serving, or marking any ticket complete. A separate idempotent, audited repair command may create only verified missing tickets after source-order validation.

## Acceptance tests for integration

1. Fictional venue A's operator cannot read, transition or reconcile venue B's tickets; unauthenticated access is denied.
2. Invalid jumps (`queued -> served`, `served -> preparing`) and non-manager ready cancellations fail without writing events.
3. Two simultaneous updates with the same expected version produce exactly one successful transition and one event.
4. Replaying an identical command is idempotent; same command ID with different payload fails.
5. Kitchen/bar views do not leak each other's station tickets to station-only roles.
6. A missing bar ticket is reported for a synthetic accepted drink order; a cancelled source order is not automatically resurrected.
7. Event and outbox writes roll back if the state update fails.

## Integration dependencies and safeguards

Before implementing HTTP routes: recover/verify actual Python persistence and order contracts; establish authenticated session, server-derived venue context, station RBAC, CSRF/origin protections for writes, and synthetic fixtures. Do not expose a public backend. Food/drink catalog Python API and minimal React integration remain a separately prioritized cross-cutting dependency. No payments, notifications, supplier actions, production data, or metered services. €0 additional spending. `main` must remain untouched.

## Run ledger

2026-11-26: this ticket lifecycle contract is the scoped deliverable; existing pure offline ticket transition/intake/reconciliation modules were verified by reading their source; this specification's persistent CAS, event/outbox transaction and manager-only ready cancellation are **not implemented or tested here**. Existing `ready -> cancelled` is forbidden in `backend/kitchen_ticket.py`, so any proposed change needs a separate reviewed milestone. No tests were executed in this run. Next distinct KDS increment: persistent CAS plus append-only event transaction against the verified offline modules, with synthetic tests; avoid re-authoring this lifecycle contract.
