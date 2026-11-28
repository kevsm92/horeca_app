import sqlite3
import unittest
from datetime import datetime, timezone
from workflow_escalation_preview import pending_review_candidates


class EscalationPreviewTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.executescript('''CREATE TABLE workflow_outbox(event_id TEXT PRIMARY KEY,
            venue_id TEXT, created_at_utc TEXT, state TEXT);
            CREATE TABLE workflow_mock_tasks(venue_id TEXT, event_id TEXT,
            check_id TEXT, sop_revision_id TEXT, status TEXT);''')
        self.db.executemany('INSERT INTO workflow_outbox VALUES(?,?,?,?)', [
            ('e1','venue-a','2026-11-24T09:00:00+00:00','delivered'),
            ('e2','venue-b','2026-11-24T08:00:00+00:00','delivered'),
            ('e3','venue-a','2026-11-24T09:00:00+00:00','pending'),
            ('e4','venue-a','2026-11-26T09:00:00+00:00','delivered')])
        self.db.executemany('INSERT INTO workflow_mock_tasks VALUES(?,?,?,?,?)', [
            ('venue-a','e1','synthetic-check-1','synthetic-rev-1','open'),
            ('venue-b','e2','synthetic-check-2','synthetic-rev-1','open'),
            ('venue-a','e3','synthetic-check-3','synthetic-rev-1','open'),
            ('venue-a','e4','synthetic-check-4','synthetic-rev-1','open')])
        self.db.commit()

    def tearDown(self): self.db.close()

    def test_tenant_and_delivery_and_time_filters(self):
        result = pending_review_candidates(self.db, venue_id='venue-a',
            as_of=datetime(2026,11,25,tzinfo=timezone.utc))
        self.assertEqual([r['event_id'] for r in result], ['e1'])
        self.assertTrue(result[0]['review_required'])

    def test_read_only_and_limit(self):
        before = self.db.total_changes
        result = pending_review_candidates(self.db, venue_id='venue-b',
            as_of=datetime(2026,11,25,tzinfo=timezone.utc), limit=1)
        self.assertEqual(len(result), 1)
        self.assertEqual(before, self.db.total_changes)

    def test_rejects_naive_time_and_invalid_limit(self):
        with self.assertRaises(ValueError):
            pending_review_candidates(self.db, venue_id='venue-a', as_of=datetime(2026,11,25))
        with self.assertRaises(ValueError):
            pending_review_candidates(self.db, venue_id='venue-a',
                as_of=datetime.now(timezone.utc), limit=True)

if __name__ == '__main__': unittest.main()
