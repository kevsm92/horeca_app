import unittest
from invoice_matching import match_invoice


class InvoiceMatchingTests(unittest.TestCase):
    def check(self, *args):
        return match_invoice('v1', 'v1', 'v1', 'v1', 'SYN-001', *args)

    def test_match(self):
        self.assertEqual(self.check(2, 2, 2, 100, 100).status, 'matched')

    def test_shortage_requires_review(self):
        self.assertEqual(self.check(3, 2, 2, 100, 100).status, 'review_required')

    def test_equal_amount_different_quantity_requires_review(self):
        self.assertEqual(self.check(2, 2, 1, 100, 200).status, 'review_required')

    def test_price_variance(self):
        r = self.check(2, 2, 2, 100, 110)
        self.assertEqual((r.variance_cents, r.status), (20, 'review_required'))

    def test_tenant_isolation(self):
        with self.assertRaises(PermissionError):
            match_invoice('v1', 'v1', 'v2', 'v1', 'SYN-001', 1, 1, 1, 1, 1)

    def test_invalid_inputs(self):
        for invalid in (-1, True, 1.5):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                self.check(invalid, 1, 1, 1, 1)


if __name__ == '__main__':
    unittest.main()
