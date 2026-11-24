"""Focused synthetic tests for offline task ledger: python -m unittest discover -s prototypes -p 'test_operational_task_ledger.py'."""
import sqlite3
import unittest
try:
    from prototypes.operational_task_ledger import TaskLedger
except ModuleNotFoundError:
    from operational_task_ledger import TaskLedger

class TaskLedgerTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.ledger = TaskLedger(self.db)
        self.ledger.create(venue='a', task='clean', title='Fictional cleaning task',
                           assignee='staff-a', priority='normal',
                           due_at='2026-11-24T15:00:00+01:00', actor='staff-a')

    def test_completion_and_audit(self):
        self.assertEqual(self.ledger.complete(venue='a', task='clean',
                         actor='staff-a', expected_revision=0), 1)
        self.assertEqual([e[0] for e in self.ledger.history(
                         venue='a', task='clean', actor='staff-a')], ['created','completed'])

    def test_cross_venue_and_unassigned_denied(self):
        for venue, actor in [('b','staff-a'),('a','staff-b')]:
            with self.assertRaises(PermissionError):
                self.ledger.complete(venue=venue, task='clean', actor=actor, expected_revision=0)

    def test_duplicate_completion_denied(self):
        self.ledger.complete(venue='a', task='clean', actor='staff-a', expected_revision=0)
        with self.assertRaises(PermissionError):
            self.ledger.complete(venue='a', task='clean', actor='staff-a', expected_revision=0)

    def test_immutable_audit(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute('DELETE FROM task_events')

    def test_naive_due_date_denied(self):
        with self.assertRaises(ValueError):
            self.ledger.create(venue='a',task='other',title='X',assignee='staff-a',
                               priority='low',due_at='2026-11-24T15:00:00',actor='staff-a')

if __name__ == '__main__':
    unittest.main()
