"""Offline goods-receiving three-way match prototype. Synthetic data only.

No inventory posting, invoice approval, supplier communications, or payments.
Run: python -m unittest discover -s prototypes/receiving -p 'test_*.py'
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class PurchaseLine:
    venue_id: str
    po_id: str
    sku: str
    ordered_qty: int
    unit_price_cents: int


@dataclass(frozen=True)
class DeliveryLine:
    venue_id: str
    po_id: str
    sku: str
    received_qty: int
    invoice_qty: int
    invoice_unit_price_cents: int


def reconcile(po: PurchaseLine, delivery: DeliveryLine) -> dict:
    """Compare quantities and integer-cent prices without changing records."""
    if not po.venue_id or not po.po_id or not po.sku:
        raise ValueError("missing purchase identity")
    if (po.venue_id, po.po_id, po.sku) != (
        delivery.venue_id, delivery.po_id, delivery.sku
    ):
        raise ValueError("cross-venue or mismatched purchase line")
    values = (po.ordered_qty, po.unit_price_cents, delivery.received_qty,
              delivery.invoice_qty, delivery.invoice_unit_price_cents)
    if any(type(v) is not int or v < 0 for v in values):
        raise ValueError("quantities and cents must be nonnegative integers")
    reasons = []
    if delivery.received_qty != po.ordered_qty:
        reasons.append("delivery_quantity_discrepancy")
    if delivery.invoice_qty != delivery.received_qty:
        reasons.append("invoice_quantity_discrepancy")
    if delivery.invoice_unit_price_cents != po.unit_price_cents:
        reasons.append("invoice_unit_price_discrepancy")
    return {
        "venue_id": po.venue_id, "po_id": po.po_id, "sku": po.sku,
        "ordered_cents": po.ordered_qty * po.unit_price_cents,
        "received_cents": delivery.received_qty * po.unit_price_cents,
        "invoiced_cents": delivery.invoice_qty * delivery.invoice_unit_price_cents,
        "quantity_shortfall": max(0, po.ordered_qty - delivery.received_qty),
        "reasons": reasons,
        "status": "requires_human_review" if reasons else "matched_for_review",
        "posted": False,
    }
