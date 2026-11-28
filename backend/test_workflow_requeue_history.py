import sqlite3
import unittest
from workflow_requeue_history import list_requeue_history


class RequeueHistoryTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.execute('''CREATE TABLE workflow_dead_letter_requeues (
            id INTEGER PRIMARY KEY AUTOINCREMENT, venue_id TEXT NOT NULL,
            event_id TEXT NOT NULL, manager_id TEXT NOT NULL,
            requeued_at_utc TEXT NOT NULL)''')
        for venue, event in [('a', 'one'), ('b', 'hidden'), ('a', 'two'), ('a', 'three')]:
            self.db.execute('''INSERT INTO workflow_dead_letter_requeues
                (venue_id,event_id,manager_id,requeued_at_utc) VALUES (?,?,?,?)''',
                (venue, event, 'synthetic-manager', '2026-11-25T12:00:00+00:00'))
        self.db.commit()

    def test_venue_isolation_pagination_and_metadata_only(self):
        first = list_requeue_history(self.db, venue_id='a', limit=2)
        self.assertEqual([r['event_id'] for r in first['items']], ['three', 'two'])
        self.assertEqual(first['next_cursor'], 3)
        second = list_requeue_history(self.db, venue_id='a', limit=2,
                                      before_id=first['next_cursor'])
        self.assertEqual([r['event_id'] for r in second['items']], ['one'])
        self.assertIsNone(second['next_cursor'])
        self.assertEqual([r['event_id'] for r in list_requeue_history(self.db, venue_id='b')['items']], ['hidden'])
        self.assertEqual(set(first['items'][0]), {'id', 'event_id', 'manager_id', 'requeued_at_utc'})

    def test_rejects_invalid_scope_and_cursor(self):
        for kwargs in ({'venue_id': ''}, {'venue_id': 'a', 'limit': 0},
                       {'venue_id': 'a', 'limit': True}, {'venue_id': 'a', 'limit': 101},
                       {'venue_id': 'a', 'before_id': 0}, {'venue_id': 'a', 'before_id': '3'}):
            with self.assertRaises(ValueError):
                list_requeue_history(self.db, **kwargs)


if __name__ == '__main__':
    unittest.main()
