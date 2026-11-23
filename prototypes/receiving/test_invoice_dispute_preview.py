import unittest
from invoice_dispute_preview import preview_invoice_dispute as preview


class InvoiceDisputeTests(unittest.TestCase):
    def call(self, **overrides):
        values = dict(venue_id="synthetic-venue", po_id="PO-SYN", sku="SYN-FLOUR",
                      received_qty=8, invoiced_qty=8, agreed_unit_cents=250,
                      invoiced_unit_cents=250)
        values.update(overrides)
        return preview(**values)

    def test_quantity_overbilling(self):
        result = self.call(invoiced_qty=10)
        self.assertEqual((result.excess_quantity, result.excess_cents), (2, 500))
        self.assertFalse(result.posted)
        self.assertEqual(result.status, "human_review_required")

    def test_price_overbilling(self):
        result = self.call(invoiced_unit_cents=300)
        self.assertEqual(result.excess_cents, 400)
        self.assertEqual(result.reasons, ("invoice_exceeds_agreed_unit_price",))

    def test_combined_excess_is_not_double_counted(self):
        result = self.call(invoiced_qty=10, invoiced_unit_cents=300)
        self.assertEqual(result.excess_cents, 1000)
        self.assertEqual(len(result.reasons), 2)

    def test_no_dispute_or_underbilling(self):
        self.assertIsNone(self.call())
        self.assertIsNone(self.call(invoiced_qty=7, invoiced_unit_cents=240))

    def test_invalid_identity_and_numbers(self):
        for value in (True, -1, 2.5, "3"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.call(invoiced_qty=value)
        with self.assertRaises(ValueError):
            self.call(venue_id=" ")
        with self.assertRaises(ValueError):
            self.call(agreed_unit_cents=0)


if __name__ == "__main__":
    unittest.main()
