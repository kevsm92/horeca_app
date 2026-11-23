"""Focused offline tests for receiving reconciliation."""
import unittest
from reconciliation import PurchaseLine, DeliveryLine, reconcile


class ReceivingTests(unittest.TestCase):
    def setUp(self):
        self.po = PurchaseLine("fictional-venue-a", "PO-001", "FLOUR", 10, 250)

    def delivery(self, **changes):
        fields = dict(venue_id="fictional-venue-a", po_id="PO-001",
                      sku="FLOUR", received_qty=10, invoice_qty=10,
                      invoice_unit_price_cents=250)
        fields.update(changes)
        return DeliveryLine(**fields)

    def test_match_does_not_post(self):
        result = reconcile(self.po, self.delivery())
        self.assertEqual(result["status"], "matched_for_review")
        self.assertFalse(result["posted"])
        self.assertEqual(result["invoiced_cents"], 2500)

    def test_short_delivery_and_invoice_difference(self):
        result = reconcile(self.po, self.delivery(received_qty=8, invoice_qty=10))
        self.assertEqual(result["quantity_shortfall"], 2)
        self.assertEqual(len(result["reasons"]), 2)

    def test_price_difference(self):
        result = reconcile(self.po, self.delivery(invoice_unit_price_cents=300))
        self.assertIn("invoice_unit_price_discrepancy", result["reasons"])

    def test_cross_venue_rejected(self):
        with self.assertRaises(ValueError):
            reconcile(self.po, self.delivery(venue_id="fictional-venue-b"))

    def test_negative_float_bool_rejected(self):
        for quantity in (-1, 1.5, True):
            with self.subTest(quantity=quantity), self.assertRaises(ValueError):
                reconcile(self.po, self.delivery(received_qty=quantity))

    def test_wrong_purchase_rejected(self):
        with self.assertRaises(ValueError):
            reconcile(self.po, self.delivery(po_id="PO-002"))


if __name__ == "__main__":
    unittest.main()
