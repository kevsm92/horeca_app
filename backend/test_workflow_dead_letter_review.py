import sqlite3
import unittest
from workflow_outbox import initialize
from workflow_dead_letter_review import list_dead_letters


class DeadLetterReviewTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        initialize(self.db)
        for i, venue in enumerate(('a', 'a', 'a', 'b')):
            self.db.execute('''INSERT INTO workflow_outbox
                (event_id,venue_id,event_type,event_version,aggregate_id,aggregate_revision,
                 payload_json,created_at_utc,available_at_utc,state,attempt_count,last_error_code)
                 VALUES (?,?,?,1,?,1,?,?,?,'dead_letter',2,'handler_failure')''',
                 (f'id{i}',venue,'operational.check_due.v1',f'check{i}',
                  '{"private":"must-not-leak"}', '2026-11-25T00:00:00+00:00',
                  '2026-11-25T00:00:00+00:00'))
        self.db.commit()

    def test_tenant_pagination_and_no_payload(self):
        first = list_dead_letters(self.db, venue_id='a', limit=2)
        self.assertEqual([x['event_id'] for x in first['items']], ['id2','id1'])
        self.assertEqual(first['next_cursor'], 'id1')
        second = list_dead_letters(self.db, venue_id='a', limit=2,
                                   before_event_id=first['next_cursor'])
        self.assertEqual([x['event_id'] for x in second['items']], ['id0'])
        self.assertIsNone(second['next_cursor'])
        self.assertNotIn('private', str(first))
        self.assertEqual([x['event_id'] for x in list_dead_letters(self.db,venue_id='b')['items']], ['id3'])

    def test_invalid_scope_and_bounds(self):
        for kwargs in ({'venue_id':''}, {'venue_id':'a','limit':101},
                       {'venue_id':'a','limit':True}, {'venue_id':'a','before_event_id':''}):
            with self.assertRaises(ValueError):
                list_dead_letters(self.db, **kwargs)


if __name__ == '__main__':
    unittest.main()
