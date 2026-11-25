import sqlite3
import unittest
from datetime import datetime, timedelta, timezone
from workflow_ack import acknowledge

NOW = datetime(2026, 11, 25, 5, tzinfo=timezone.utc)

class AckTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.execute("""CREATE TABLE workflow_outbox(event_id TEXT PRIMARY KEY, venue_id TEXT,
          state TEXT, lease_token TEXT, lease_expires_at_utc TEXT, last_error_code TEXT)""")
        self.db.execute('INSERT INTO workflow_outbox VALUES (?,?,?,?,?,?)',
                        ('e1', 'venue-a', 'leased', 'token-new',
                         (NOW + timedelta(minutes=1)).isoformat(), 'RETRY'))
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def ack(self, **overrides):
        args = dict(venue_id='venue-a', event_id='e1', lease_token='token-new', now=NOW)
        return acknowledge(self.db, **(args | overrides))

    def test_success_and_idempotent_replay(self):
        self.assertTrue(self.ack())
        self.assertFalse(self.ack())
        self.assertEqual(self.db.execute('SELECT state,lease_token,last_error_code FROM workflow_outbox').fetchone(),
                         ('delivered', None, None))

    def test_stale_token_and_wrong_venue(self):
        self.assertFalse(self.ack(lease_token='token-old'))
        self.assertFalse(self.ack(venue_id='venue-b'))
        self.assertEqual(self.db.execute('SELECT state FROM workflow_outbox').fetchone()[0], 'leased')

    def test_expiry_is_exclusive(self):
        self.assertFalse(self.ack(now=NOW + timedelta(minutes=1)))
        self.assertFalse(self.ack(now=NOW + timedelta(minutes=2)))

    def test_reject_naive_and_existing_transaction(self):
        with self.assertRaises(ValueError):
            self.ack(now=NOW.replace(tzinfo=None))
        self.db.execute('UPDATE workflow_outbox SET last_error_code=?', ('TEMP',))
        with self.assertRaises(ValueError):
            self.ack()
        self.db.rollback()

if __name__ == '__main__':
    unittest.main()
