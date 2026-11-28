"""Offline synthetic goods-receiving reconciliation reference; no stock posting."""
from dataclasses import dataclass
import unittest

@dataclass(frozen=True)
class PurchaseLine:
    sku: str
    units: int
    unit_cents: int

@dataclass(frozen=True)
class DeliveryLine:
    sku: str
    units: int

def reconcile(venue, po_venue, ordered, delivered):
    """Return discrepancy tuples (SKU, ordered, received), plus totals in cents."""
    if not venue or venue != po_venue or not ordered:
        raise ValueError("missing venue/order or tenant mismatch")
    if len({x.sku for x in ordered}) != len(ordered) or len({x.sku for x in delivered}) != len(delivered):
        raise ValueError("duplicate SKU")
    if any(not x.sku or x.units <= 0 or x.unit_cents < 0 for x in ordered):
        raise ValueError("invalid PO line")
    if any(not x.sku or x.units < 0 for x in delivered):
        raise ValueError("invalid delivery line")
    prices = {x.sku: x.unit_cents for x in ordered}
    if any(x.sku not in prices for x in delivered):
        raise ValueError("unmatched SKU requires review")
    received = {x.sku: x.units for x in delivered}
    discrepancies = tuple((x.sku, x.units, received.get(x.sku, 0)) for x in ordered if x.units != received.get(x.sku, 0))
    expected_cents = sum(x.units * x.unit_cents for x in ordered)
    received_cents = sum(received.get(x.sku, 0) * x.unit_cents for x in ordered)
    return {"status": "review_required" if discrepancies else "matched_unposted",
            "discrepancies": discrepancies, "expected_cents": expected_cents,
            "received_cents": received_cents}

class Tests(unittest.TestCase):
    def setUp(self):
        self.po = (PurchaseLine("SYN-1", 5, 120),)
    def test_exact(self):
        self.assertEqual(reconcile("v1", "v1", self.po, (DeliveryLine("SYN-1", 5),))["status"], "matched_unposted")
    def test_short(self):
        self.assertEqual(reconcile("v1", "v1", self.po, (DeliveryLine("SYN-1", 3),))["discrepancies"], (("SYN-1", 5, 3),))
    def test_over(self):
        self.assertEqual(reconcile("v1", "v1", self.po, (DeliveryLine("SYN-1", 6),))["status"], "review_required")
    def test_missing(self):
        self.assertEqual(reconcile("v1", "v1", self.po, ())["received_cents"], 0)
    def test_tenant(self):
        with self.assertRaises(ValueError):
            reconcile("v1", "v2", self.po, ())
    def test_unknown_sku(self):
        with self.assertRaises(ValueError):
            reconcile("v1", "v1", self.po, (DeliveryLine("OTHER", 1),))
    def test_duplicate(self):
        with self.assertRaises(ValueError):
            reconcile("v1", "v1", self.po, (DeliveryLine("SYN-1", 1), DeliveryLine("SYN-1", 2)))
    def test_negative(self):
        with self.assertRaises(ValueError):
            reconcile("v1", "v1", self.po, (DeliveryLine("SYN-1", -1),))

if __name__ == "__main__":
    unittest.main()
