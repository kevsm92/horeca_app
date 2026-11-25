import sqlite3
import unittest
from datetime import datetime, timedelta, timezone
from workflow_due_preview import preview_due


class PreviewTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.execute('''CREATE TABLE workflow_outbox (
            event_id TEXT, venue_id TEXT, event_type TEXT, available_at_utc TEXT,
            attempt_count INTEGER, state TEXT, lease_expires_at_utc TEXT,
            payload_json TEXT, lease_token TEXT)''')
        self.now = datetime(2026, 11, 25, 17, tzinfo=timezone.utc)
        for eid, venue, state, due, expiry in [
            ('a', 'v1', 'pending', -2, None),
            ('b', 'v1', 'leased', -1, -1),
            ('c', 'v1', 'leased', -1, 1),
            ('d', 'v1', 'dead_letter', -1, None),
            ('e', 'v2', 'pending', -1, None),
            ('f', 'v1', 'pending', 1, None),
        ]:
            stamp = lambda mins: (self.now + timedelta(minutes=mins)).isoformat()
            self.db.execute('INSERT INTO workflow_outbox VALUES (?,?,?,?,?,?,?,?,?)',
                (eid, venue, 'operational.check_due.v1', stamp(due), 2, state,
                 stamp(expiry) if expiry is not None else None,
                 '{"private":"never return"}', 'secret-lease'))
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_due_order_and_expired_lease_only(self):
        result = preview_due(self.db, venue_id='v1', now=self.now)
        self.assertEqual([r['event_id'] for r in result], ['a', 'b'])
        self.assertEqual([r['reason'] for r in result], ['pending', 'expired_lease'])
        self.assertNotIn('payload_json', str(result))
        self.assertNotIn('secret-lease', str(result))

    def test_venue_limit_and_no_mutations(self):
        before = self.db.total_changes
        self.assertEqual([r['event_id'] for r in preview_due(self.db, venue_id='v2', now=self.now)], ['e'])
        self.assertEqual([r['event_id'] for r in preview_due(self.db, venue_id='v1', now=self.now, limit=1)], ['a'])
        self.assertEqual(self.db.total_changes, before)

    def test_rejects_bad_context(self):
        for kwargs in ({'venue_id':'', 'now':self.now},
                       {'venue_id':'v1','now':datetime(2026,11,25)},
                       {'venue_id':'v1','now':self.now,'limit':True},
                       {'venue_id':'v1','now':self.now,'limit':101}):
            with self.assertRaises(ValueError):
                preview_due(self.db, **kwargs)


if __name__ == '__main__':
    unittest.main()
