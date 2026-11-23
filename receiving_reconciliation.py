"""Offline synthetic goods-receipt reconciliation; no stock posting or supplier actions."""
from dataclasses import dataclass


@dataclass(frozen=True)
class ReceiptLine:
    venue_id: str
    purchase_order_id: str
    sku: str
    ordered_units: int
    delivered_units: int
    accepted_units: int
    unit_price_cents: int


@dataclass(frozen=True)
class Reconciliation:
    short_units: int
    rejected_units: int
    over_units: int
    accepted_value_cents: int
    discrepancy: bool


def reconcile(line: ReceiptLine, *, venue_id: str) -> Reconciliation:
    """Calculate discrepancies without silently booking stock or creating credits."""
    if not venue_id or not line.venue_id or venue_id != line.venue_id:
        raise PermissionError("venue mismatch")
    if not line.purchase_order_id or not line.sku:
        raise ValueError("purchase order and SKU required")
    values = (line.ordered_units, line.delivered_units, line.accepted_units, line.unit_price_cents)
    if any(type(value) is not int or value < 0 for value in values):
        raise ValueError("quantities and price must be nonnegative integers")
    if line.accepted_units > line.delivered_units:
        raise ValueError("accepted quantity exceeds delivered quantity")
    short = max(0, line.ordered_units - line.delivered_units)
    over = max(0, line.delivered_units - line.ordered_units)
    rejected = line.delivered_units - line.accepted_units
    return Reconciliation(short, rejected, over, line.accepted_units * line.unit_price_cents,
                          bool(short or rejected or over))
