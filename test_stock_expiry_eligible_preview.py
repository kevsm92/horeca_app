import unittest
from datetime import datetime, timedelta, timezone
from stock_expiry_eligible_preview import preview_eligible_stock

NOW = datetime(2026, 11, 20, 14, tzinfo=timezone.utc)


def batch(batch_id, quantity, **kwargs):
    return {'venue_id': 'a', 'batch_id': batch_id, 'quantity_units': quantity, **kwargs}


class EligibleStockTests(unittest.TestCase):
    def check(self, batches):
        return preview_eligible_stock(venue_id='a', batches=batches, inspected_at=NOW)

    def test_withholds_expired_unknown_and_near_expiry(self):
        result = self.check([batch('safe', 9, original_use_by=NOW + timedelta(days=3)),
                             batch('expired', 4, original_use_by=NOW),
                             batch('unknown', 3),
                             batch('soon', 2, original_use_by=NOW + timedelta(hours=1))])
        self.assertEqual((result['eligible_units'], result['withheld_units']), (9, 9))
        self.assertEqual([r['status'] for r in result['review_batches']],
                         ['expired', 'unknown_deadline', 'expiring_soon'])
        self.assertFalse(result['ledger_modified'])
        self.assertFalse(result['purchase_order_created'])

    def test_original_deadline_precedence(self):
        result = self.check([batch('a', 7, original_use_by=NOW - timedelta(days=1),
                                   discard_at=NOW + timedelta(days=5))])
        self.assertEqual(result['eligible_units'], 0)

    def test_tenant_mismatch(self):
        with self.assertRaises(PermissionError):
            self.check([dict(batch('a', 1), venue_id='b')])

    def test_duplicate_batch(self):
        with self.assertRaises(ValueError):
            self.check([batch('a', 1), batch('a', 1)])

    def test_negative_and_boolean_quantity(self):
        for quantity in (-1, True):
            with self.subTest(quantity=quantity), self.assertRaises(ValueError):
                self.check([batch('a', quantity)])

    def test_naive_inspection_time(self):
        with self.assertRaises(ValueError):
            preview_eligible_stock(venue_id='a', batches=[batch('a', 1)],
                                   inspected_at=datetime(2026, 11, 20))

    def test_empty_batches(self):
        self.assertEqual(self.check([])['eligible_units'], 0)


if __name__ == '__main__':
    unittest.main()
