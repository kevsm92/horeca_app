import unittest
from datetime import datetime, timedelta, timezone
from roster_presence import project_presence


class PresenceTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 27, 6, tzinfo=timezone.utc)
        self.event = dict(venue_id='v1', staff_id='fictional-1', event_id='e1',
                          occurred_at=self.now - timedelta(minutes=20), source='kiosk', kind='in')

    def project(self, events):
        return project_presence(venue_id='v1', staff_ids=['fictional-1', 'fictional-2'],
                                events=events, as_of=self.now)['staff']

    def test_unknown_is_not_scheduled_presence(self):
        self.assertEqual(self.project([])[0]['presence'], 'unknown')

    def test_kiosk_in_out_and_unknown(self):
        out = dict(self.event, event_id='e2', kind='out', occurred_at=self.now)
        self.assertEqual(self.project([out, self.event])[0]['presence'], 'clocked_out')
        self.assertEqual(self.project([self.event])[0]['presence'], 'clocked_in')
        self.assertEqual(self.project([self.event])[1]['presence'], 'unknown')

    def test_tenant_and_future_events_ignored(self):
        foreign = dict(self.event, venue_id='v2')
        future = dict(self.event, occurred_at=self.now + timedelta(seconds=1))
        self.assertEqual(self.project([foreign, future])[0]['presence'], 'unknown')

    def test_reject_non_kiosk_and_duplicates(self):
        with self.assertRaises(ValueError):
            self.project([dict(self.event, source='mobile')])
        with self.assertRaises(ValueError):
            self.project([self.event, self.event])

    def test_naive_timestamp_rejected(self):
        with self.assertRaises(ValueError):
            self.project([dict(self.event, occurred_at=self.now.replace(tzinfo=None))])


if __name__ == '__main__':
    unittest.main()
