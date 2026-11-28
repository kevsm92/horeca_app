"""Focused synthetic tests for offline operational tasks."""
import sqlite3
import unittest
from backend.operations_tasks import initialize, create_task, complete_task, list_tasks

AT = '2026-11-24T11:00:00+01:00'

class TaskTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        initialize(self.db)
        create_task(self.db, venue_id='fictional-a', task_id='t1',
                    title='Check fridge log', actor_id='manager-1',
                    occurred_at=AT, assignee_id='staff-1', priority='high', due_at=AT)

    def tearDown(self):
        self.db.close()

    def test_tenant_isolation(self):
        self.assertEqual(list_tasks(self.db, venue_id='fictional-b'), [])
        self.assertFalse(complete_task(self.db, venue_id='fictional-b',
                         task_id='t1', actor_id='other', occurred_at=AT))
        self.assertEqual(list_tasks(self.db, venue_id='fictional-a')[0][-1], 'open')

    def test_completion_is_idempotent_and_audited(self):
        args = dict(venue_id='fictional-a', task_id='t1',
                    actor_id='staff-1', occurred_at=AT)
        self.assertTrue(complete_task(self.db, **args))
        self.assertFalse(complete_task(self.db, **args))
        self.assertEqual(self.db.execute(
            'SELECT action FROM task_events ORDER BY event_id').fetchall(),
            [('created',), ('completed',)])

    def test_audit_is_append_only(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("DELETE FROM task_events WHERE task_id='t1'")

    def test_timezone_required(self):
        with self.assertRaises(ValueError):
            complete_task(self.db, venue_id='fictional-a', task_id='t1',
                          actor_id='staff-1', occurred_at='2026-11-24T11:00:00')

    def test_invalid_priority_is_atomic(self):
        with self.assertRaises(sqlite3.IntegrityError):
            create_task(self.db, venue_id='fictional-a', task_id='bad',
                        title='Bad', actor_id='manager-1',
                        occurred_at=AT, priority='urgent')
        self.assertEqual(self.db.execute(
            "SELECT COUNT(*) FROM task_events WHERE task_id='bad'").fetchone()[0], 0)

if __name__ == '__main__':
    unittest.main()
