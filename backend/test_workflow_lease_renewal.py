import sqlite3
import unittest
from datetime import datetime, timedelta, timezone
from workflow_lease_renewal import renew_lease


class LeaseRenewalTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.execute('''CREATE TABLE workflow_outbox (
            venue_id TEXT, event_id TEXT, state TEXT, lease_token TEXT,
            lease_expires_at_utc TEXT)''')
        self.now = datetime(2026, 11, 25, 20, tzinfo=timezone.utc)
        self.db.execute('INSERT INTO workflow_outbox VALUES (?,?,?,?,?)',
                        ('synthetic-a','synthetic-event','leased','token',
                         (self.now+timedelta(seconds=30)).isoformat()))
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def renew(self, **overrides):
        kwargs = dict(venue_id='synthetic-a', event_id='synthetic-event',
                      lease_token='token', now=self.now, lease_seconds=90)
        kwargs.update(overrides)
        return renew_lease(self.db, **kwargs)

    def test_extends_owned_lease(self):
        self.assertTrue(self.renew())
        expiry = self.db.execute('SELECT lease_expires_at_utc FROM workflow_outbox').fetchone()[0]
        self.assertEqual(expiry, (self.now+timedelta(seconds=90)).isoformat())

    def test_rejects_wrong_venue_token_expired_or_delivered(self):
        self.assertFalse(self.renew(venue_id='synthetic-b'))
        self.assertFalse(self.renew(lease_token='wrong'))
        self.assertFalse(self.renew(now=self.now+timedelta(seconds=31)))
        self.db.execute("UPDATE workflow_outbox SET state='delivered'")
        self.db.commit()
        self.assertFalse(self.renew())

    def test_invalid_input_and_transaction(self):
        for override in ({'now':datetime(2026,11,25)}, {'lease_seconds':True},
                         {'lease_seconds':0}, {'event_id':''}):
            with self.assertRaises(ValueError):
                self.renew(**override)
        self.db.execute('BEGIN')
        with self.assertRaises(ValueError):
            self.renew()
        self.db.rollback()


if __name__ == '__main__':
    unittest.main()
