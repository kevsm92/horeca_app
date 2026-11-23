"""Offline synthetic goods receiving reconciliation; no stock posting or payments."""
from dataclasses import dataclass


@dataclass(frozen=True)
class OrderedLine:
    sku: str
    quantity: int
    unit_price_cents: int


@dataclass(frozen=True)
class DeliveredLine:
    sku: str
    quantity: int


@dataclass(frozen=True)
class Discrepancy:
    sku: str
    ordered: int
    received: int
    difference: int
    estimated_credit_cents: int


def reconcile(venue_id: str, po_venue_id: str, delivery_venue_id: str,
              ordered: tuple[OrderedLine, ...],
              delivered: tuple[DeliveredLine, ...]) -> tuple[Discrepancy, ...]:
    """Compare distinct SKUs. Over-delivery is flagged, never auto-credited."""
    if not venue_id or venue_id != po_venue_id or venue_id != delivery_venue_id:
        raise PermissionError("venue mismatch")
    order_map, delivery_map = {}, {}
    for line in ordered:
        if (not line.sku or type(line.quantity) is not int
                or type(line.unit_price_cents) is not int or line.quantity < 0
                or line.unit_price_cents < 0 or line.sku in order_map):
            raise ValueError("invalid or duplicate purchase-order line")
        order_map[line.sku] = line
    for line in delivered:
        if (not line.sku or type(line.quantity) is not int or line.quantity < 0
                or line.sku in delivery_map):
            raise ValueError("invalid or duplicate delivery line")
        delivery_map[line.sku] = line.quantity
    results = []
    for sku in sorted(order_map.keys() | delivery_map.keys()):
        line = order_map.get(sku)
        expected = line.quantity if line else 0
        actual = delivery_map.get(sku, 0)
        if expected != actual:
            results.append(Discrepancy(
                sku, expected, actual, actual - expected,
                max(expected - actual, 0) * line.unit_price_cents if line else 0))
    return tuple(results)
