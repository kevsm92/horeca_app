"""Synthetic regression tests for the offline notification audit projection."""
import sqlite3
import unittest
from reservation_notification_mock import initialize, enqueue_mock
from reservation_notification_read_model import list_mock_intents


class ReadModelTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(':memory:', isolation_level=None)
        initialize(self.conn)
        for venue, event in [('venue-a', 'e2'), ('venue-b', 'e0'), ('venue-a', 'e1')]:
            enqueue_mock(self.conn, venue_id=venue, event_id=event,
                         kind='waitlist_offer', reservation_id='synthetic-r',
                         payload={'scheduled_utc': '2026-11-16T08:00:00+00:00'})

    def tearDown(self):
        self.conn.close()

    def test_tenant_isolation_and_order(self):
        self.assertEqual([x['event_id'] for x in list_mock_intents(self.conn, venue_id='venue-a')], ['e1', 'e2'])
        self.assertEqual([x['event_id'] for x in list_mock_intents(self.conn, venue_id='venue-b')], ['e0'])

    def test_bounded_page(self):
        self.assertEqual(len(list_mock_intents(self.conn, venue_id='venue-a', limit=1)), 1)
        for limit in (0, 101, True, 1.5, '2'):
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                list_mock_intents(self.conn, venue_id='venue-a', limit=limit)

    def test_rejects_empty_venue(self):
        for venue in ('', ' ', None, 3):
            with self.subTest(venue=venue), self.assertRaises(ValueError):
                list_mock_intents(self.conn, venue_id=venue)

    def test_read_only_and_offline(self):
        before = self.conn.total_changes
        result = list_mock_intents(self.conn, venue_id='venue-a')
        self.assertEqual(self.conn.total_changes, before)
        self.assertEqual({x['state'] for x in result}, {'mock_pending'})
        self.assertEqual(set(result[0]), {'event_id', 'kind', 'reservation_id', 'scheduled_utc', 'state'})
        self.assertNotIn('recipient', str(result))


if __name__ == '__main__':
    unittest.main()
