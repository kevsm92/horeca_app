"""Offline, venue-scoped goods receipt reconciliation prototype (synthetic only).

No supplier communication, stock posting, invoice payment or external I/O.
Amounts are integer euro cents. A discrepancy requires human review.
"""
from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class PurchaseLine:
    venue_id: str
    purchase_order_id: str
    sku: str
    ordered_units: int
    unit_price_cents: int


@dataclass(frozen=True)
class DeliveryLine:
    venue_id: str
    purchase_order_id: str
    sku: str
    delivered_units: int
    invoiced_units: int
    invoice_unit_price_cents: int


@dataclass(frozen=True)
class Reconciliation:
    venue_id: str
    sku: str
    ordered_cents: int
    received_cents: int
    invoice_cents: int
    quantity_variance: int
    invoice_variance_cents: int
    status: str
    reasons: Tuple[str, ...]


def reconcile(purchase: PurchaseLine, delivery: DeliveryLine) -> Reconciliation:
    """Three-way line comparison; no automatic credit, approval or ledger mutation."""
    if not purchase.venue_id or not purchase.purchase_order_id or not purchase.sku:
        raise ValueError("missing purchase identity")
    if (purchase.venue_id, purchase.purchase_order_id, purchase.sku) != (
        delivery.venue_id, delivery.purchase_order_id, delivery.sku
    ):
        raise ValueError("venue/order/SKU mismatch")
    numbers = (purchase.ordered_units, purchase.unit_price_cents,
               delivery.delivered_units, delivery.invoiced_units,
               delivery.invoice_unit_price_cents)
    if any(type(n) is not int or n < 0 for n in numbers):
        raise ValueError("quantities and prices must be nonnegative integers")
    if purchase.ordered_units == 0:
        raise ValueError("purchase order line must have positive quantity")
    reasons = []
    if delivery.delivered_units != purchase.ordered_units:
        reasons.append("delivery_quantity_differs_from_order")
    if delivery.invoiced_units != delivery.delivered_units:
        reasons.append("invoice_quantity_differs_from_delivery")
    if delivery.invoice_unit_price_cents != purchase.unit_price_cents:
        reasons.append("invoice_unit_price_differs_from_order")
    received_cents = delivery.delivered_units * purchase.unit_price_cents
    invoice_cents = delivery.invoiced_units * delivery.invoice_unit_price_cents
    return Reconciliation(
        venue_id=purchase.venue_id, sku=purchase.sku,
        ordered_cents=purchase.ordered_units * purchase.unit_price_cents,
        received_cents=received_cents, invoice_cents=invoice_cents,
        quantity_variance=delivery.delivered_units - purchase.ordered_units,
        invoice_variance_cents=invoice_cents - received_cents,
        status="review_required" if reasons else "matched_unposted",
        reasons=tuple(reasons),
    )


if __name__ == "__main__":
    import unittest

    class ReconciliationTests(unittest.TestCase):
        def setUp(self):
            self.po = PurchaseLine("fictional-venue-a", "PO-1", "SYN-FLOUR", 10, 250)

        def test_exact_match_is_unposted(self):
            result = reconcile(self.po, DeliveryLine("fictional-venue-a", "PO-1", "SYN-FLOUR", 10, 10, 250))
            self.assertEqual((result.status, result.invoice_cents, result.reasons), ("matched_unposted", 2500, ()))

        def test_short_delivery_and_invoice_discrepancy(self):
            result = reconcile(self.po, DeliveryLine("fictional-venue-a", "PO-1", "SYN-FLOUR", 8, 9, 300))
            self.assertEqual(result.status, "review_required")
            self.assertEqual(result.quantity_variance, -2)
            self.assertEqual(result.invoice_variance_cents, 700)
            self.assertEqual(len(result.reasons), 3)

        def test_cross_venue_rejected(self):
            with self.assertRaisesRegex(ValueError, "mismatch"):
                reconcile(self.po, DeliveryLine("fictional-venue-b", "PO-1", "SYN-FLOUR", 10, 10, 250))

        def test_invalid_amounts_rejected(self):
            with self.assertRaises(ValueError):
                reconcile(self.po, DeliveryLine("fictional-venue-a", "PO-1", "SYN-FLOUR", -1, 10, 250))
            with self.assertRaises(ValueError):
                reconcile(self.po, DeliveryLine("fictional-venue-a", "PO-1", "SYN-FLOUR", True, 10, 250))

    unittest.main(verbosity=2)
