import unittest
from datetime import datetime, timedelta, timezone
from manager_kpi_freshness import annotate_freshness


class FreshnessTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 28, 6, 0, tzinfo=timezone.utc)
        self.snapshot = {'venue_id': 'fictional-venue-a', 'is_live': False, 'metric': {'status': 'unavailable', 'value': None}}

    def test_recent_preserves_unavailable_and_offline(self):
        result = annotate_freshness(snapshot=self.snapshot, observed_at=self.now, as_of=self.now)
        self.assertEqual(result['freshness']['status'], 'recent_offline')
        self.assertIsNone(result['metric']['value'])
        self.assertFalse(result['is_live'])

    def test_stale_is_not_live(self):
        result = annotate_freshness(snapshot=self.snapshot, observed_at=self.now-timedelta(seconds=301), as_of=self.now)
        self.assertEqual(result['freshness']['status'], 'stale')
        self.assertFalse(result['is_live'])

    def test_future_and_naive_rejected(self):
        for observed in (self.now+timedelta(seconds=1), self.now.replace(tzinfo=None)):
            with self.assertRaises(ValueError):
                annotate_freshness(snapshot=self.snapshot, observed_at=observed, as_of=self.now)

    def test_rejects_live_or_missing_venue(self):
        for snapshot in ({'venue_id': 'a', 'is_live': True}, {'venue_id': '', 'is_live': False}):
            with self.assertRaises(ValueError):
                annotate_freshness(snapshot=snapshot, observed_at=self.now, as_of=self.now)

    def test_threshold_boundary(self):
        result = annotate_freshness(snapshot=self.snapshot, observed_at=self.now-timedelta(seconds=300), as_of=self.now)
        self.assertEqual(result['freshness']['status'], 'recent_offline')

if __name__ == '__main__':
    unittest.main()
