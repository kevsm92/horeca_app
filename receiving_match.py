"""Offline three-way receiving reconciliation; never approves invoices or orders."""
from dataclasses import dataclass


@dataclass(frozen=True)
class MatchResult:
    status: str
    ordered_qty: int
    received_qty: int
    invoiced_qty: int
    expected_cents: int
    invoice_cents: int
    reasons: tuple[str, ...]


def reconcile(*, ordered_qty: int, received_qty: int, invoiced_qty: int,
              unit_price_cents: int, invoice_unit_price_cents: int,
              accepted_qty: int | None = None) -> MatchResult:
    """Single-SKU PO/receipt/invoice comparison in integer units and EUR cents."""
    values = (ordered_qty, received_qty, invoiced_qty, unit_price_cents,
              invoice_unit_price_cents)
    if any(type(v) is not int or v < 0 for v in values):
        raise ValueError('quantities and prices must be nonnegative integers')
    if accepted_qty is None:
        accepted_qty = received_qty
    if type(accepted_qty) is not int or not 0 <= accepted_qty <= received_qty:
        raise ValueError('accepted quantity must be within received quantity')
    reasons = []
    if received_qty > ordered_qty:
        reasons.append('over_delivery')
    elif received_qty < ordered_qty:
        reasons.append('short_delivery')
    if accepted_qty < received_qty:
        reasons.append('rejected_goods')
    if invoiced_qty != accepted_qty:
        reasons.append('invoice_quantity_mismatch')
    if invoice_unit_price_cents != unit_price_cents:
        reasons.append('invoice_price_mismatch')
    return MatchResult('review_required' if reasons else 'matched', ordered_qty,
                       received_qty, invoiced_qty, accepted_qty * unit_price_cents,
                       invoiced_qty * invoice_unit_price_cents, tuple(reasons))
