import unittest
from receiving import OrderedLine, DeliveredLine, reconcile


class ReceivingTests(unittest.TestCase):
    def test_shortage_and_unexpected_goods(self):
        got = reconcile('v1', 'v1', 'v1', (OrderedLine('milk', 5, 299),),
                        (DeliveredLine('milk', 3), DeliveredLine('extra', 2)))
        self.assertEqual([(x.sku, x.difference, x.estimated_credit_cents) for x in got],
                         [('extra', 2, 0), ('milk', -2, 598)])

    def test_exact_delivery(self):
        self.assertEqual(reconcile('v', 'v', 'v', (OrderedLine('a', 2, 50),),
                                   (DeliveredLine('a', 2),)), ())

    def test_cross_venue_denied(self):
        with self.assertRaises(PermissionError):
            reconcile('v1', 'v2', 'v1', (), ())

    def test_duplicate_and_negative_rejected(self):
        with self.assertRaises(ValueError):
            reconcile('v', 'v', 'v', (OrderedLine('a', 1, 20), OrderedLine('a', 1, 20)), ())
        with self.assertRaises(ValueError):
            reconcile('v', 'v', 'v', (), (DeliveredLine('a', -1),))

    def test_bool_not_quantity(self):
        with self.assertRaises(ValueError):
            reconcile('v', 'v', 'v', (OrderedLine('a', True, 10),), ())


if __name__ == '__main__':
    unittest.main()
