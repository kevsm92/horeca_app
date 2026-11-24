import sqlite3
import unittest
from backend.operations_tasks import initialize, create_task, complete_task
from backend.task_assignment import assign_task

T = '2026-11-24T20:00:00+01:00'

class TaskAssignmentTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        initialize(self.db)
        for venue in ('a', 'b'):
            create_task(self.db, venue_id=venue, task_id='t', title='Synthetic check',
                        actor_id='manager', occurred_at=T)

    def test_venue_scoped_assignment_and_idempotent_noop(self):
        self.assertTrue(assign_task(self.db, venue_id='a', task_id='t', actor_id='manager', assignee_id='staff1', occurred_at=T))
        self.assertFalse(assign_task(self.db, venue_id='a', task_id='t', actor_id='manager', assignee_id='staff1', occurred_at=T))
        self.assertEqual(self.db.execute("SELECT assignee_id FROM tasks WHERE venue_id='b'").fetchone(), (None,))
        self.assertEqual(self.db.execute("SELECT count(*) FROM task_events WHERE venue_id='a' AND action='assigned'").fetchone()[0], 1)

    def test_invalid_and_completed_rejected_without_event(self):
        with self.assertRaises(ValueError):
            assign_task(self.db, venue_id='a', task_id='missing', actor_id='manager', assignee_id='s', occurred_at=T)
        complete_task(self.db, venue_id='a', task_id='t', actor_id='manager', occurred_at=T)
        with self.assertRaises(ValueError):
            assign_task(self.db, venue_id='a', task_id='t', actor_id='manager', assignee_id='s', occurred_at=T)
        self.assertEqual(self.db.execute("SELECT count(*) FROM task_events WHERE action='assigned'").fetchone()[0], 0)

    def test_timestamp_validation_and_immutable_audit(self):
        with self.assertRaises(ValueError):
            assign_task(self.db, venue_id='a', task_id='t', actor_id='manager', assignee_id='s', occurred_at='2026-11-24T20:00:00')
        assign_task(self.db, venue_id='a', task_id='t', actor_id='manager', assignee_id='s', occurred_at=T)
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("DELETE FROM task_events WHERE action='assigned'")

if __name__ == '__main__':
    unittest.main()
