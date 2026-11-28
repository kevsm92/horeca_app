import sqlite3
import unittest
from datetime import datetime, timezone
from workflow_dead_letter import initialize, requeue_dead_letter


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.execute("""CREATE TABLE workflow_outbox (
            event_id TEXT PRIMARY KEY, venue_id TEXT, state TEXT,
            available_at_utc TEXT, attempt_count INTEGER,
            lease_token TEXT, lease_expires_at_utc TEXT, last_error_code TEXT)""")
        initialize(self.db)
        self.db.execute("INSERT INTO workflow_outbox VALUES ('e1','v1','dead_letter','old',3,NULL,NULL,'handler_rejected')")
        self.db.commit()
        self.now = datetime(2026, 11, 25, 12, 0, tzinfo=timezone.utc)

    def recover(self, venue='v1', event='e1'):
        return requeue_dead_letter(self.db, venue_id=venue, event_id=event,
                                   manager_id='synthetic-manager', now=self.now)

    def test_requeues_and_audits_once(self):
        self.assertTrue(self.recover())
        self.assertEqual(self.db.execute('SELECT state,attempt_count,last_error_code FROM workflow_outbox').fetchone(), ('pending',0,None))
        self.assertFalse(self.recover())
        self.assertEqual(self.db.execute('SELECT count(*) FROM workflow_dead_letter_requeues').fetchone()[0],1)

    def test_cross_venue_denied(self):
        self.assertFalse(self.recover(venue='v2'))
        self.assertEqual(self.db.execute('SELECT state FROM workflow_outbox').fetchone()[0], 'dead_letter')

    def test_invalid_time_and_actor(self):
        with self.assertRaises(ValueError):
            requeue_dead_letter(self.db,venue_id='v1',event_id='e1',manager_id='',now=self.now)
        with self.assertRaises(ValueError):
            requeue_dead_letter(self.db,venue_id='v1',event_id='e1',manager_id='m',now=datetime(2026,11,25))

    def test_audit_failure_rolls_back(self):
        self.db.execute('DROP TABLE workflow_dead_letter_requeues')
        with self.assertRaises(sqlite3.OperationalError):
            self.recover()
        self.assertEqual(self.db.execute('SELECT state FROM workflow_outbox').fetchone()[0], 'dead_letter')

if __name__ == '__main__':
    unittest.main()
