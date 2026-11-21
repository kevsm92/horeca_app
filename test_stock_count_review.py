import unittest
from datetime import datetime, timezone, timedelta
from stock_count_review import review_count

T = datetime(2026, 11, 20, 11, tzinfo=timezone.utc)

class ReviewTests(unittest.TestCase):
    def call(self, **kw):
        return review_count(ledger_units=10, counted_units=8, unit='each', counted_at=T, **kw)
    def test_discrepancy_needs_review(self):
        self.assertEqual(self.call()['status'], 'pending_review')
    def test_partial_review_still_pending(self):
        self.assertEqual(self.call(reviewer_id='manager')['status'], 'pending_review')
    def test_documented_not_approved(self):
        result = self.call(reviewed_at=T + timedelta(minutes=1), reviewer_id='manager', reason='Recount requested')
        self.assertEqual(result['status'], 'review_documented')
        self.assertFalse(result['approved'])
        self.assertFalse(result['posted'])
    def test_matched_no_adjustment(self):
        result = review_count(ledger_units=8, counted_units=8, unit='each', counted_at=T)
        self.assertEqual(result['status'], 'matched')
        self.assertFalse(result['posted'])
    def test_backdated_review_rejected(self):
        with self.assertRaises(ValueError):
            self.call(reviewed_at=T - timedelta(seconds=1), reviewer_id='manager', reason='recount')
    def test_naive_count_rejected(self):
        with self.assertRaises(ValueError):
            review_count(ledger_units=1, counted_units=2, unit='g', counted_at=datetime(2026, 11, 20))
    def test_invalid_quantity_rejected(self):
        with self.assertRaises(ValueError):
            review_count(ledger_units=1, counted_units=True, unit='g', counted_at=T)
    def test_overlong_reason_rejected(self):
        with self.assertRaises(ValueError):
            self.call(reviewed_at=T, reviewer_id='manager', reason='x'*1001)

if __name__ == '__main__': unittest.main()
