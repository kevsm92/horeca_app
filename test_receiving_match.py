import unittest
from receiving_match import reconcile


class ReceivingMatchTests(unittest.TestCase):
    def test_exact_match(self):
        r = reconcile(ordered_qty=4, received_qty=4, invoiced_qty=4,
                      unit_price_cents=125, invoice_unit_price_cents=125)
        self.assertEqual((r.status, r.expected_cents, r.invoice_cents), ('matched', 500, 500))

    def test_short_delivery_and_invoice_discrepancy(self):
        r = reconcile(ordered_qty=5, received_qty=3, invoiced_qty=5,
                      unit_price_cents=100, invoice_unit_price_cents=110)
        self.assertEqual(r.reasons, ('short_delivery', 'invoice_quantity_mismatch', 'invoice_price_mismatch'))

    def test_rejected_goods_not_payable(self):
        r = reconcile(ordered_qty=3, received_qty=3, accepted_qty=2, invoiced_qty=3,
                      unit_price_cents=100, invoice_unit_price_cents=100)
        self.assertEqual(r.expected_cents, 200)
        self.assertIn('rejected_goods', r.reasons)

    def test_overdelivery(self):
        r = reconcile(ordered_qty=1, received_qty=2, invoiced_qty=2,
                      unit_price_cents=50, invoice_unit_price_cents=50)
        self.assertIn('over_delivery', r.reasons)

    def test_invalid_values(self):
        with self.assertRaises(ValueError):
            reconcile(ordered_qty=True, received_qty=1, invoiced_qty=1,
                      unit_price_cents=1, invoice_unit_price_cents=1)
        with self.assertRaises(ValueError):
            reconcile(ordered_qty=1, received_qty=1, accepted_qty=2, invoiced_qty=1,
                      unit_price_cents=1, invoice_unit_price_cents=1)


if __name__ == '__main__':
    unittest.main()
