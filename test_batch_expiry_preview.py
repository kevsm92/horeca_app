import unittest
from datetime import datetime, timedelta, timezone
from batch_expiry_preview import preview_batch_expiry

NOW = datetime(2026, 11, 20, 12, tzinfo=timezone.utc)

class BatchExpiryTests(unittest.TestCase):
    def check(self, **kwargs):
        return preview_batch_expiry(inspected_at=NOW, **kwargs)

    def test_missing_deadline_unresolved(self):
        self.assertEqual(self.check()['status'], 'unknown_deadline')
    def test_expired_at_boundary(self):
        self.assertEqual(self.check(discard_at=NOW)['status'], 'expired')
    def test_original_use_by_never_extended(self):
        result = self.check(discard_at=NOW + timedelta(days=3), original_use_by=NOW - timedelta(hours=1))
        self.assertEqual(result['status'], 'expired')
        self.assertEqual(result['effective_deadline'], NOW - timedelta(hours=1))
    def test_post_opening_deadline_takes_priority(self):
        result = self.check(discard_at=NOW + timedelta(hours=2), original_use_by=NOW + timedelta(days=5))
        self.assertEqual(result['effective_deadline'], NOW + timedelta(hours=2))
    def test_warning_boundary(self):
        self.assertEqual(self.check(discard_at=NOW + timedelta(days=1))['status'], 'expiring_soon')
    def test_healthy(self):
        self.assertEqual(self.check(discard_at=NOW + timedelta(days=4))['status'], 'within_deadline')
    def test_naive_date_rejected(self):
        with self.assertRaises(ValueError): self.check(discard_at=datetime(2026, 11, 21))
    def test_bad_warning_rejected(self):
        with self.assertRaises(ValueError): self.check(warning_minutes=True)
    def test_no_automatic_disposal(self):
        self.assertFalse(self.check(discard_at=NOW - timedelta(days=1))['disposed'])

if __name__ == '__main__': unittest.main()
