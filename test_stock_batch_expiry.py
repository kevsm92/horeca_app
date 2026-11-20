import unittest
from datetime import datetime, timedelta, timezone
from stock_batch_expiry import classify_batch

T = datetime(2026, 11, 20, 10, tzinfo=timezone.utc)


class BatchExpiryTests(unittest.TestCase):
    def test_unopened_before_manufacturer_deadline(self):
        self.assertEqual(classify_batch(now=T, manufacturer_use_by=T + timedelta(days=1))['status'], 'within_recorded_deadline')

    def test_original_deadline_cannot_be_extended(self):
        r = classify_batch(now=T, manufacturer_use_by=T - timedelta(minutes=1), opened_at=T - timedelta(days=1), post_open_discard=T + timedelta(days=2))
        self.assertEqual(r['status'], 'expired')
        self.assertTrue(r['requires_manual_review'])

    def test_post_open_deadline_shortens_manufacturer_deadline(self):
        r = classify_batch(now=T, manufacturer_use_by=T + timedelta(days=5), opened_at=T - timedelta(days=2), post_open_discard=T)
        self.assertEqual(r['status'], 'expired')

    def test_missing_rule_not_pass(self):
        self.assertEqual(classify_batch(now=T, manufacturer_use_by=T + timedelta(days=1), opened_at=T)['status'], 'missing_post_open_rule')

    def test_future_opening_untrusted(self):
        self.assertEqual(classify_batch(now=T, manufacturer_use_by=T + timedelta(days=2), opened_at=T + timedelta(hours=1))['status'], 'untrusted_opening')

    def test_invalid_post_open_deadline(self):
        self.assertEqual(classify_batch(now=T, manufacturer_use_by=T + timedelta(days=2), opened_at=T, post_open_discard=T - timedelta(hours=1))['status'], 'invalid_post_open_deadline')

    def test_naive_time_rejected(self):
        with self.assertRaises(ValueError):
            classify_batch(now=T.replace(tzinfo=None), manufacturer_use_by=T)

    def test_unopened_cannot_have_post_open_deadline(self):
        with self.assertRaises(ValueError):
            classify_batch(now=T, manufacturer_use_by=T, post_open_discard=T)

    def test_exact_deadline_is_expired(self):
        self.assertEqual(classify_batch(now=T, manufacturer_use_by=T)['status'], 'expired')


if __name__ == '__main__':
    unittest.main()
