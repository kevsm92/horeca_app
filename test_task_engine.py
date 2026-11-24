import sqlite3
import unittest
from task_engine import initialize, create_task, complete_task, list_tasks

class TaskTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(':memory:')
        initialize(self.db)
    def test_venue_isolation_and_completion(self):
        create_task(self.db,venue_id='a',task_id='1',title='Check fridge',actor_id='mgr')
        create_task(self.db,venue_id='b',task_id='1',title='Clean station',actor_id='mgr')
        with self.assertRaises(ValueError):
            complete_task(self.db,venue_id='a',task_id='missing',actor_id='mgr')
        complete_task(self.db,venue_id='a',task_id='1',actor_id='mgr')
        self.assertEqual(list_tasks(self.db,venue_id='a')[0][5],'completed')
        self.assertEqual(list_tasks(self.db,venue_id='b')[0][5],'open')
        with self.assertRaises(ValueError):
            complete_task(self.db,venue_id='a',task_id='1',actor_id='mgr')
        self.assertEqual(self.db.execute('SELECT count(*) FROM task_events').fetchone()[0],3)
    def test_audit_immutable(self):
        create_task(self.db,venue_id='a',task_id='1',title='Inspect',actor_id='mgr')
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute('DELETE FROM task_events')
    def test_validation(self):
        with self.assertRaises(ValueError):
            create_task(self.db,venue_id='a',task_id='1',title=' ',actor_id='mgr')
        with self.assertRaises(sqlite3.IntegrityError):
            create_task(self.db,venue_id='a',task_id='1',title='Valid',actor_id='mgr',priority='urgent')
        self.assertEqual(list_tasks(self.db,venue_id='a'),[])
if __name__=='__main__': unittest.main()
