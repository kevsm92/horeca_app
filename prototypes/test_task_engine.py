"""Focused offline tests: python -m unittest discover -s prototypes -p 'test_*.py'"""
import sqlite3
import unittest
from task_engine import connect, create_task, complete_task, list_tasks

class TaskEngineTests(unittest.TestCase):
    def setUp(self):
        self.db=connect()
        create_task(self.db,venue_id='fictional-a',task_id='t1',title='Clean demo fridge',actor_id='demo-manager')
    def tearDown(self):
        self.db.close()
    def test_tenant_isolation(self):
        self.assertEqual(list_tasks(self.db,venue_id='fictional-b'),[])
        with self.assertRaises(ValueError):
            complete_task(self.db,venue_id='fictional-b',task_id='t1',actor_id='demo-manager',expected_revision=0)
    def test_duplicate_and_stale_completion(self):
        complete_task(self.db,venue_id='fictional-a',task_id='t1',actor_id='demo-worker',expected_revision=0)
        with self.assertRaises(ValueError):
            complete_task(self.db,venue_id='fictional-a',task_id='t1',actor_id='demo-worker',expected_revision=0)
        self.assertEqual(list_tasks(self.db,venue_id='fictional-a')[0][-2:],('completed',1))
    def test_immutable_events(self):
        for sql in ('UPDATE task_events SET action="forged"', 'DELETE FROM task_events'):
            with self.assertRaises(sqlite3.IntegrityError):
                self.db.execute(sql)
    def test_timezone_due_date(self):
        with self.assertRaises(ValueError):
            create_task(self.db,venue_id='fictional-a',task_id='t2',title='Check',actor_id='demo',due_at='2026-11-24T10:00:00')
    def test_invalid_priority(self):
        with self.assertRaises(sqlite3.IntegrityError):
            create_task(self.db,venue_id='fictional-a',task_id='t2',title='Check',actor_id='demo',priority='urgent-now')

if __name__=='__main__':
    unittest.main()
