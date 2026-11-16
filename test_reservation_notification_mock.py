"""Synthetic-only tests for reservation notification mock."""
import sqlite3
import unittest
from reservation_notification_mock import initialize, enqueue_mock

class MockNotificationTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(':memory:')
        initialize(self.conn)
        self.args = dict(venue_id='v1',event_id='e1',kind='waitlist_offer',reservation_id='r1',payload={'scheduled_utc':'2026-11-16T12:00:00+00:00'})
    def tearDown(self):
        self.conn.close()
    def test_insert_and_replay(self):
        self.assertTrue(enqueue_mock(self.conn,**self.args))
        self.assertFalse(enqueue_mock(self.conn,**self.args))
        self.assertEqual(self.conn.execute('select state from reservation_notification_intents').fetchone()[0],'mock_pending')
    def test_conflicting_replay(self):
        enqueue_mock(self.conn,**self.args)
        with self.assertRaises(ValueError):
            enqueue_mock(self.conn,**{**self.args,'reservation_id':'r2'})
    def test_tenant_isolation(self):
        enqueue_mock(self.conn,**self.args)
        self.assertTrue(enqueue_mock(self.conn,**{**self.args,'venue_id':'v2'}))
        self.assertEqual(self.conn.execute('select count(*) from reservation_notification_intents').fetchone()[0],2)
    def test_reject_recipient_and_non_utc(self):
        for payload in ({'scheduled_utc':'2026-11-16T12:00:00+00:00','email':'a@b.test'},{'scheduled_utc':'2026-11-16T12:00:00'}):
            with self.assertRaises(ValueError):
                enqueue_mock(self.conn,**{**self.args,'payload':payload})
    def test_no_external_delivery_fields(self):
        enqueue_mock(self.conn,**self.args)
        cols=[r[1] for r in self.conn.execute('pragma table_info(reservation_notification_intents)')]
        self.assertNotIn('email',cols)
        self.assertNotIn('phone',cols)

if __name__=='__main__':
    unittest.main()
