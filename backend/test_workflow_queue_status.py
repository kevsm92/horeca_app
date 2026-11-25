import sqlite3
import unittest
from datetime import datetime, timezone, timedelta
from workflow_outbox import initialize
from workflow_queue_status import queue_status


class QueueStatusTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        initialize(self.db)
        self.now = datetime(2026, 11, 25, 14, tzinfo=timezone.utc)
        for ident, venue, state, offset, lease_offset in (
            ('1', 'a', 'pending', -1, None),
            ('2', 'a', 'pending', 1, None),
            ('3', 'a', 'leased', -1, -1),
            ('4', 'a', 'leased', -1, 1),
            ('5', 'a', 'dead_letter', -1, None),
            ('6', 'b', 'pending', -1, None),
        ):
            stamp = lambda n: (self.now + timedelta(minutes=n)).isoformat()
            self.db.execute("""INSERT INTO workflow_outbox
                (event_id,venue_id,event_type,event_version,aggregate_id,aggregate_revision,
                 payload_json,created_at_utc,available_at_utc,state,lease_expires_at_utc)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (ident,venue,'operational.check_due.v1',1,ident,1,'{}',stamp(-2),
                 stamp(offset),state,stamp(lease_offset) if lease_offset is not None else None))
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_counts_and_due_leases(self):
        self.assertEqual(queue_status(self.db, venue_id='a', now=self.now),
            {'counts': {'pending':2,'leased':2,'delivered':0,'dead_letter':1},
             'actionable_now':2})

    def test_tenant_isolation_and_empty(self):
        self.assertEqual(queue_status(self.db, venue_id='b', now=self.now)['actionable_now'],1)
        self.assertEqual(queue_status(self.db, venue_id='c', now=self.now)['actionable_now'],0)
        self.assertEqual(queue_status(self.db, venue_id='c', now=self.now)['counts']['pending'],0)

    def test_rejects_invalid_context_and_is_read_only(self):
        for venue, now in (('', self.now), ('a', datetime(2026,11,25)), ('a', None)):
            with self.assertRaises(ValueError):
                queue_status(self.db, venue_id=venue, now=now)
        before = self.db.total_changes
        queue_status(self.db, venue_id='a', now=self.now)
        self.assertEqual(before, self.db.total_changes)


if __name__ == '__main__':
    unittest.main()
