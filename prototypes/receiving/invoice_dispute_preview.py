"""Synthetic, offline invoice overbilling dispute preview; never posts or contacts vendors."""
from dataclasses import dataclass


@dataclass(frozen=True)
class InvoiceDisputePreview:
    venue_id: str
    po_id: str
    sku: str
    excess_quantity: int
    excess_cents: int
    reasons: tuple[str, ...]
    status: str = "human_review_required"
    posted: bool = False


def preview_invoice_dispute(*, venue_id: str, po_id: str, sku: str,
                            received_qty: int, invoiced_qty: int,
                            agreed_unit_cents: int, invoiced_unit_cents: int
                            ) -> InvoiceDisputePreview | None:
    """Flag invoice excess over accepted delivery at agreed PO price.

    A price discrepancy and quantity discrepancy may coexist. Excess is
    max(0, invoiced total - received quantity * agreed unit price).
    Negative differences are not automatically credits or approvals.
    """
    if any(type(v) is not str or not v.strip() for v in (venue_id, po_id, sku)):
        raise ValueError("missing purchase identity")
    numbers = (received_qty, invoiced_qty, agreed_unit_cents, invoiced_unit_cents)
    if any(type(v) is not int or v < 0 for v in numbers):
        raise ValueError("quantities and cents must be nonnegative integers")
    if agreed_unit_cents == 0:
        raise ValueError("agreed price must be positive")
    reasons = []
    if invoiced_qty > received_qty:
        reasons.append("invoice_exceeds_received_quantity")
    if invoiced_unit_cents > agreed_unit_cents:
        reasons.append("invoice_exceeds_agreed_unit_price")
    excess = max(0, invoiced_qty * invoiced_unit_cents - received_qty * agreed_unit_cents)
    if not reasons or excess == 0:
        return None
    return InvoiceDisputePreview(venue_id, po_id, sku, max(0, invoiced_qty - received_qty), excess, tuple(reasons))
