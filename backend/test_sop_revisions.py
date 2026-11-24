import sqlite3
import unittest
from backend.sop_revisions import initialize, approve_revision, get_revision

class SopRevisionTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        initialize(self.db)
        self.args = dict(venue_id='fictional-a', sop_id='chiller', author_id='writer',
                         approver_id='reviewer', station='kitchen', content='Synthetic checklist')

    def test_append_and_isolation(self):
        self.assertEqual(approve_revision(self.db, **self.args, expected_previous_revision=0), 1)
        self.assertIsNone(get_revision(self.db, venue_id='fictional-b', sop_id='chiller', revision=1))
        self.assertEqual(approve_revision(self.db, **{**self.args,'content':'Revised synthetic checklist'},
                                          expected_previous_revision=1), 2)
        self.assertEqual(get_revision(self.db, venue_id='fictional-a', sop_id='chiller', revision=1)[2],
                         'Synthetic checklist')

    def test_stale_and_self_approval_rejected(self):
        approve_revision(self.db, **self.args, expected_previous_revision=0)
        with self.assertRaises(ValueError):
            approve_revision(self.db, **self.args, expected_previous_revision=0)
        with self.assertRaises(ValueError):
            approve_revision(self.db, **{**self.args, 'approver_id':'writer'}, expected_previous_revision=1)

    def test_immutable(self):
        approve_revision(self.db, **self.args, expected_previous_revision=0)
        for sql in ('UPDATE sop_revisions SET content=? WHERE venue_id=?',
                    'DELETE FROM sop_revisions WHERE content=? AND venue_id=?'):
            with self.assertRaises(sqlite3.IntegrityError):
                self.db.execute(sql, ('Synthetic checklist','fictional-a'))

if __name__ == '__main__':
    unittest.main()
