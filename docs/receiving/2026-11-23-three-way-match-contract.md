# Three-way receiving reconciliation — v1 contract
Date: 2026-11-23 Europe/Brussels. Architecture-only milestone; source implementation and tests have not been recovered.

## Boundary
Offline comparison of approved purchase-order lines, accepted delivery receipts and supplier invoice lines. No real supplier contact, stock posting, accounting export or payment.
Derive venue ID from authenticated server session; require receiving:review permission. All PO, receipt and invoice records must belong to the same venue and supplier. Reject mismatches without exposing cross-tenant records.

## Inputs
PO line: immutable ID, venue, supplier, approved revision, canonical unit, ordered quantity, EUR unit price in integer cents.
Receipt: immutable ID, PO line, accepted and rejected quantities, timestamp, actor, idempotency key.
Invoice line: immutable ID, supplier, PO line, invoiced quantity, canonical unit, EUR unit price in integer cents, revision.
Reject negative quantities, floating point currency, unapproved POs, unknown units and implicit conversions.

## Assessment
Sum distinct accepted receipt quantities; rejected quantities do not count. Compare invoice quantity against accepted receipts, not ordered quantity. Report all applicable exceptions: INVOICE_QTY_EXCEEDS_ACCEPTED, INVOICE_QTY_BELOW_ACCEPTED, UNIT_PRICE_MISMATCH, OVER_RECEIPT, UNAPPROVED_PO, IDENTITY_MISMATCH, INVALID_UNIT. No tolerance in v1. An exact match is MATCHED_FOR_REVIEW, never payment approval. Partial delivery without invoice is AWAITING_INVOICE.
Persist append-only assessments referencing exact source revisions, differences, actor, timestamp and SHA-256 of canonical payload. New evidence creates a new assessment, never overwrites history. Any exception requires explicit human resolution and reassessment. Proposed supplier credit is internal draft only.
Use transaction-level idempotency uniqueness (venue, source, event ID), optimistic PO revision checks and atomic acceptance. Never count duplicate receipt events twice.

## Synthetic acceptance cases
1. PO 10 at 500 cents; accepted 4+6; invoice 10 at 500: MATCHED_FOR_REVIEW.
2. PO 10; accepted 4; invoice 10: INVOICE_QTY_EXCEEDS_ACCEPTED by 6.
3. PO 10 at 500; accepted 10; invoice 10 at 550: UNIT_PRICE_MISMATCH by 50 cents per unit.
4. Replay same receipt event: no extra accepted quantity.
5. Venue B invoice against venue A PO: denied, no venue A details returned.
6. Two concurrent revision updates: stale one rejected with conflict.

## Next dependency
Recover actual develop source and previous receiving tests before choosing integration paths. Implement these cases as focused automated tests, including role denial, tenant isolation and rollback, before any HTTP exposure. No production deployment, real data, paid service or external action is authorized.