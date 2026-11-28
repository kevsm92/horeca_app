import sqlite3
import unittest
from datetime import datetime, timedelta, timezone
from workflow_outbox import initialize, produce
from workflow_claim import claim_due
from workflow_retry import fail_lease

NOW = datetime(2026, 11, 25, 8, 0, tzinfo=timezone.utc)

class RetryTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        initialize(self.db)
        produce(self.db, venue_id='synthetic-a', event_type='operational.check_due.v1',
                aggregate_id='synthetic-check', aggregate_revision=1,
                payload={'check_id':'synthetic-check','sop_revision_id':'synthetic-r1'},
                mutate=lambda db: None)
        self.db.execute('UPDATE workflow_outbox SET available_at_utc=?',
                        ((NOW-timedelta(seconds=1)).isoformat(),))
        self.db.commit()

    def fail(self, lease, now=NOW, **kw):
        return fail_lease(self.db, venue_id='synthetic-a', event_id=lease['event_id'],
                          lease_token=lease['lease_token'], now=now,
                          error_code='handler_transient', **kw)

    def test_retry_backoff_and_dead_letter(self):
        first = claim_due(self.db, venue_id='synthetic-a', now=NOW)
        self.assertEqual(self.fail(first), 'pending')
        self.assertIsNone(claim_due(self.db, venue_id='synthetic-a', now=NOW))
        second = claim_due(self.db, venue_id='synthetic-a', now=NOW+timedelta(seconds=30))
        self.assertIsNotNone(second)
        self.assertEqual(self.fail(second, NOW+timedelta(seconds=30)), 'pending')
        third = claim_due(self.db, venue_id='synthetic-a', now=NOW+timedelta(seconds=90))
        self.assertEqual(self.fail(third, NOW+timedelta(seconds=90)), 'dead_letter')
        self.assertIsNone(claim_due(self.db, venue_id='synthetic-a', now=NOW+timedelta(days=2)))
        self.assertEqual(self.db.execute('SELECT attempt_count,last_error_code FROM workflow_outbox').fetchone(),
                         (3, 'handler_transient'))

    def test_wrong_venue_stale_token_and_permanent_rejection(self):
        lease = claim_due(self.db, venue_id='synthetic-a', now=NOW)
        self.assertIsNone(fail_lease(self.db, venue_id='synthetic-b', event_id=lease['event_id'],
            lease_token=lease['lease_token'], now=NOW, error_code='handler_transient'))
        self.assertEqual(self.fail(lease), 'pending')
        self.assertIsNone(self.fail(lease))
        second = claim_due(self.db, venue_id='synthetic-a', now=NOW+timedelta(seconds=30))
        self.assertEqual(fail_lease(self.db, venue_id='synthetic-a', event_id=second['event_id'],
            lease_token=second['lease_token'], now=NOW+timedelta(seconds=30),
            error_code='handler_rejected'), 'dead_letter')

    def test_validation_and_expired_lease(self):
        lease = claim_due(self.db, venue_id='synthetic-a', now=NOW)
        self.assertIsNone(self.fail(lease, NOW+timedelta(seconds=61)))
        with self.assertRaises(ValueError): fail_lease(self.db, venue_id='synthetic-a', event_id=lease['event_id'], lease_token=lease['lease_token'], now=NOW, error_code='bad')
        with self.assertRaises(ValueError): self.fail(lease, max_attempts=0)
        with self.assertRaises(ValueError): self.fail(lease, NOW.replace(tzinfo=None))

if __name__ == '__main__': unittest.main()
