"""Focused offline tests; fictional identifiers only."""
import unittest
from receiving_reconciliation import ReceiptLine, reconcile


class ReconciliationTests(unittest.TestCase):
    def line(self, **changes):
        fields = dict(venue_id="fictional-venue-a", purchase_order_id="po-demo-1",
                      sku="fictional-milk", ordered_units=10, delivered_units=8,
                      accepted_units=7, unit_price_cents=199)
        fields.update(changes)
        return ReceiptLine(**fields)

    def test_shortage_and_rejection_are_separate(self):
        result = reconcile(self.line(), venue_id="fictional-venue-a")
        self.assertEqual((result.short_units, result.rejected_units, result.over_units,
                          result.accepted_value_cents, result.discrepancy), (2, 1, 0, 1393, True))

    def test_overdelivery_is_not_silently_accepted(self):
        result = reconcile(self.line(delivered_units=12, accepted_units=10), venue_id="fictional-venue-a")
        self.assertEqual((result.over_units, result.rejected_units), (2, 2))

    def test_exact_receipt(self):
        self.assertFalse(reconcile(self.line(delivered_units=10, accepted_units=10),
                                   venue_id="fictional-venue-a").discrepancy)

    def test_cross_venue_denied(self):
        with self.assertRaises(PermissionError):
            reconcile(self.line(), venue_id="fictional-venue-b")

    def test_overacceptance_denied(self):
        with self.assertRaises(ValueError):
            reconcile(self.line(accepted_units=9), venue_id="fictional-venue-a")

    def test_negative_and_boolean_denied(self):
        for invalid in (-1, True, 1.5):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                reconcile(self.line(unit_price_cents=invalid), venue_id="fictional-venue-a")


if __name__ == "__main__":
    unittest.main()
