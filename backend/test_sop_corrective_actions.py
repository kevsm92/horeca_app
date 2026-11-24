import sqlite3
import unittest
from backend.sop_revisions import approve_revision
from backend.sop_inspections import record_check
from backend.sop_corrective_actions import initialize, record_action, list_actions


class CorrectiveActionTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        initialize(self.db)
        for venue in ('v1','v2'):
            approve_revision(self.db, venue_id=venue, sop_id='fridge',
                             author_id='author', approver_id='manager',
                             station='kitchen', content='Synthetic inspection',
                             expected_previous_revision=0)
        self.failed = record_check(self.db, venue_id='v1', sop_id='fridge',
            revision=1, actor_id='worker', equipment_id='unit-1',
            outcome='fail', exception_note='Out of approved range')
        self.passed = record_check(self.db, venue_id='v1', sop_id='fridge',
            revision=1, actor_id='worker', equipment_id='unit-2', outcome='pass')

    def tearDown(self):
        self.db.close()

    def test_action_preserves_failed_inspection(self):
        key = record_action(self.db, venue_id='v1', inspection_id=self.failed,
                            actor_id='worker', description='Quarantine stock')
        self.assertEqual(list_actions(self.db, venue_id='v1', inspection_id=self.failed)[0][0], key)
        self.assertEqual(self.db.execute('SELECT outcome FROM sop_inspections WHERE inspection_id=?',
                                         (self.failed,)).fetchone()[0], 'fail')

    def test_cross_venue_and_missing_inspection_rejected(self):
        for venue in ('v2','v3'):
            with self.assertRaises(ValueError):
                record_action(self.db, venue_id=venue, inspection_id=self.failed,
                              actor_id='worker', description='Attempt')

    def test_passing_inspection_rejected(self):
        with self.assertRaises(ValueError):
            record_action(self.db, venue_id='v1', inspection_id=self.passed,
                          actor_id='worker', description='Unnecessary')

    def test_action_immutable(self):
        key = record_action(self.db, venue_id='v1', inspection_id=self.failed,
                            actor_id='worker', description='Isolate affected food')
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute('UPDATE sop_corrective_actions SET description=? WHERE action_id=?', ('changed',key))
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute('DELETE FROM sop_corrective_actions WHERE action_id=?', (key,))

    def test_empty_description_rejected(self):
        with self.assertRaises(ValueError):
            record_action(self.db, venue_id='v1', inspection_id=self.failed,
                          actor_id='worker', description='  ')


if __name__ == '__main__':
    unittest.main()
