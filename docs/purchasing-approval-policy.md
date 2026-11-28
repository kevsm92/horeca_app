# Purchasing approval boundary — offline prototype specification

Status: architecture only; 2026-11-22 Europe/Brussels. No verified executable purchasing service is available in the inspected repository paths. Synthetic data only.

## Scope
One venue-scoped purchase requisition may be promoted into an **offline purchase-order draft** only after explicit authorized approval. No supplier communication, financial commitment, payment or live ordering occurs. A draft is not a placed order.

## Records and trust boundaries
- `requisition`: immutable UUID, `venue_id` (server-derived), creator staff ID, currency EUR, integer-cent line estimates, supplier ID, line SKU/quantity/unit, created timestamp, status, revision.
- `approval_decision`: requisition ID, venue ID, actor ID, role at decision time, decision (`approved` or `rejected`), revision, UTC timestamp, reason; append-only.
- `po_draft`: UUID, venue ID, requisition ID, approved revision, supplier snapshot, integer-cent totals, `offline_only=true`, status `draft`; unique constraint on (venue_id, requisition_id, approved_revision).
- Venue ID is never trusted from a client payload; every lookup and mutation is scoped to authenticated venue membership. Reject cross-venue references even when identifiers exist.

## State machine
`draft -> submitted -> approved | rejected`; `rejected -> draft` requires a new revision and an audit event. `approved -> po_draft` is a local transaction only. Editing submitted lines creates a new revision and invalidates prior approval. No transition sends a supplier message.

## Approval policy
- Require active authenticated manager or purchasing-approver grant for the same venue, distinct from the requester (separation of duties).
- Explicit approval thresholds are venue-configured and human-approved; absent configuration fails closed (no approval), rather than inventing euro limits.
- Reject zero/negative quantities, invalid units, negative prices, arithmetic overflow, missing supplier mappings, cross-venue suppliers and duplicate line IDs.
- Recompute totals server-side in integer cents; reject stale revision and idempotently return the same draft for repeated promotion.
- Record immutable decision history; never silently overwrite rejection or approval.

## Transaction and concurrency
SQLite implementation should use foreign keys, CHECK constraints, uniqueness, `BEGIN IMMEDIATE`, optimistic revision match and atomic insert of approval/draft/audit. Concurrent approvals of the same revision yield at most one draft; an authorization failure creates neither a draft nor an approval event. External side effects are forbidden.

## Synthetic acceptance tests (to implement before claiming code complete)
1. Authorized same-venue approver approves a submitted requisition and creates exactly one offline draft.
2. Repeated promotion and concurrent calls return the same draft, never duplicate.
3. Requester self-approval, unprivileged staff, revoked grant, unauthenticated actor and cross-venue actor are denied.
4. Edited or stale requisition revision cannot use an old approval.
5. Missing threshold configuration fails closed; threshold exceeding delegated authority requires higher human approval.
6. Invalid quantities, prices, supplier mapping and integer overflow fail without partial writes.
7. Simulated SQLite failure rolls back approval, draft and audit together.
8. Assert no network call, email, supplier order, payment or production data is used.

## Next dependency
Inspect actual Python/SQLite schema and tests from the latest verified `develop` checkout, implement migration and domain tests, then integrate authenticated API only after session/RBAC/tenant-isolation gates. Menu catalog Python API remains the higher-priority cross-cutting integration; this document does not claim that integration exists.

## Safety
No public deployment, external supplier order, live integration, credentials, charges, or personal data. This is an engineering design, not an operational procurement approval.
