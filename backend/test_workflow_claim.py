import sqlite3
import unittest
from datetime import datetime, timedelta, timezone
from workflow_claim import claim_due
from workflow_outbox import initialize, produce

NOW = datetime(2026, 11, 25, 4, 0, tzinfo=timezone.utc)

class ClaimTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        initialize(self.db)
        for venue in ('synthetic-a', 'synthetic-b'):
            produce(self.db, venue_id=venue, event_type='operational.check_due.v1',
                    aggregate_id='synthetic-check', aggregate_revision=1,
                    payload={'check_id':'synthetic-check','sop_revision_id':'synthetic-r1'},
                    mutate=lambda db: None)
        self.db.execute('UPDATE workflow_outbox SET available_at_utc=?',
                        ((NOW-timedelta(minutes=1)).isoformat(),))
        self.db.commit()

    def test_claim_scoped_and_no_duplicate_before_expiry(self):
        a = claim_due(self.db,venue_id='synthetic-a',now=NOW)
        self.assertIsNotNone(a)
        self.assertIsNone(claim_due(self.db,venue_id='synthetic-a',now=NOW))
        b = claim_due(self.db,venue_id='synthetic-b',now=NOW)
        self.assertNotEqual(a['event_id'],b['event_id'])

    def test_expired_lease_reclaimed_with_new_token(self):
        first = claim_due(self.db,venue_id='synthetic-a',now=NOW)
        again = claim_due(self.db,venue_id='synthetic-a',now=NOW+timedelta(seconds=61))
        self.assertEqual(first['event_id'],again['event_id'])
        self.assertNotEqual(first['lease_token'],again['lease_token'])
        self.assertEqual(self.db.execute('SELECT attempt_count FROM workflow_outbox WHERE event_id=?',
                                         (first['event_id'],)).fetchone()[0],2)

    def test_invalid_inputs(self):
        for kwargs in ({'venue_id':'','now':NOW}, {'venue_id':'synthetic-a','now':NOW.replace(tzinfo=None)},
                       {'venue_id':'synthetic-a','now':NOW,'lease_seconds':0}):
            with self.assertRaises(ValueError): claim_due(self.db,**kwargs)

if __name__ == '__main__': unittest.main()
