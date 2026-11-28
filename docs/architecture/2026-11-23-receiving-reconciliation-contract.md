# Goods receiving: discrepancy and three-way matching contract (2026-11-23)

Status: **standalone design only; not implemented or tested**. The reachable `develop` README identifies an initialization repository and says historic sprint archives are not included. Searches for receiving, purchase and menu_items returned no files. Do not infer the purchase-order, stock-ledger or HTTP implementations exist.

## Scoped milestone: immutable receiving reconciliation contract

All records are fictional and venue-scoped. Money is integer EUR cents; quantity is a positive integer in a **purchase-line-specific smallest unit** (e.g. grams or individual units). Never compare different units without an explicit approved conversion revision.

### Input records
- `PurchaseLine(venue_id, po_id, line_id, supplier_sku, ordered_qty, unit, unit_price_cents, currency='EUR', approved_revision)`.
- `ReceiptEvent(venue_id, receipt_id, line_id, event_id, received_qty, accepted_qty, rejected_qty, occurred_at_utc, recorded_at_utc, actor_id, evidence_ref?)`; require `received_qty == accepted_qty + rejected_qty`, all nonnegative, and stable idempotency key `(venue_id,event_id)`.
- `InvoiceLine(venue_id, invoice_id, invoice_line_id, line_id, billed_qty, unit_price_cents, currency)`.
- `MatchDecision(venue_id, po_id, line_id, receipt_event_ids, invoice_line_ids, status, variance_qty, variance_cents, reviewer_id?, reviewed_at_utc?)`.

### Deterministic projection
1. Verify caller's authenticated server-derived venue and explicit receiving permission before reading any PO, receipt or invoice. Reject cross-venue references; never accept a request-supplied venue as authority.
2. Read one PO revision and its receipt/invoice events in one consistent SQLite transaction. Deduplicate receipt events by unique key; reject conflicting replay payloads.
3. Compute `accepted_total = sum(accepted_qty)`, `rejected_total = sum(rejected_qty)`, `billed_total = sum(billed_qty)`. Reject negative quantities, currency mismatch, invalid unit, overflow or missing PO line. Flag over-receipt rather than silently increasing ordered quantity.
4. Compute `quantity_variance = billed_total - accepted_total` and `price_variance_cents = sum(billed_qty * billed_unit_price_cents) - sum(billed_qty * approved_po_unit_price_cents)`; no floating-point money.
5. Status is `pending_receipt` if no receipt, `pending_invoice` if no invoice, `discrepancy` if rejected goods, over-receipt, quantity or price variance, otherwise `matched`. These are **internal** statuses, not approvals for payment.
6. Store discrepancy cases and reviewer decisions as append-only events. A credit-note expectation is a draft record only; no supplier contact, accounting posting, stock movement or payment occurs in this milestone.
7. Future accepted-stock posting must use a distinct idempotent ledger transaction and must never include rejected goods.

### Minimum implementation tests
- Exact PO/accepted receipt/invoice -> matched, zero variance.
- Short delivery, rejected goods, over-delivery, price mismatch and missing invoice -> expected nonmatched statuses.
- Same event replay -> no duplicate receipt; conflicting replay -> rejected.
- Cross-venue PO/receipt/invoice reference -> denied without disclosure.
- Nonnegative quantities, currency, unit and integer-cent arithmetic including large values.
- Simultaneous duplicate receipt submissions -> one persisted event only.
- No external network calls or supplier communications.

### Dependencies and next slice
Recover and inspect verified Python SQLite purchasing/stock models and existing tests before integration. Implement the immutable receipt event table and unique venue/event constraint as the next narrowly scoped feature, with focused tenant and idempotency tests. Do not expose a public API until session authentication, authorization, CSRF and tenant isolation have been verified. No deployment or external integrations authorized. This design does not constitute an invoice payment authorization or legal compliance certification.
