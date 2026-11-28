"""Offline synthetic-only delivery reconciliation. No stock mutation or supplier contact."""
from dataclasses import dataclass

@dataclass(frozen=True)
class OrderedLine:
    sku: str
    ordered_units: int
    unit_price_cents: int

@dataclass(frozen=True)
class DeliveredLine:
    sku: str
    received_units: int

def reconcile(ordered: list[OrderedLine], delivered: list[DeliveredLine]) -> list[dict]:
    """Compare already-authorized venue PO lines to a delivery, without posting stock."""
    if len({x.sku for x in ordered}) != len(ordered):
        raise ValueError("duplicate ordered SKU")
    if len({x.sku for x in delivered}) != len(delivered):
        raise ValueError("duplicate delivered SKU")
    for x in ordered:
        if not x.sku or type(x.ordered_units) is not int or x.ordered_units < 0 or type(x.unit_price_cents) is not int or x.unit_price_cents < 0:
            raise ValueError("invalid ordered line")
    for x in delivered:
        if not x.sku or type(x.received_units) is not int or x.received_units < 0:
            raise ValueError("invalid delivered line")
    orders = {x.sku: x for x in ordered}
    receipts = {x.sku: x for x in delivered}
    result = []
    for sku in sorted(orders.keys() | receipts.keys()):
        order = orders.get(sku)
        receipt = receipts.get(sku)
        expected = order.ordered_units if order else 0
        actual = receipt.received_units if receipt else 0
        status = ("unexpected_sku" if order is None else
                  "short" if actual < expected else
                  "excess" if actual > expected else "matched")
        result.append({"sku": sku, "ordered_units": expected,
                       "received_units": actual, "variance_units": actual - expected,
                       "status": status,
                       "variance_value_cents": (actual - expected) * order.unit_price_cents if order else None})
    return result
