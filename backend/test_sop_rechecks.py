"""Synthetic venue-scoped deviation recheck tests."""
import sqlite3
import unittest
from backend.sop_rechecks import initialize, link_recheck

class RecheckTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        initialize(self.db)
        self.db.execute("INSERT INTO sop_revisions VALUES ('v','s',1,'a','m','kitchen','text','digest','2026-11-24T08:00:00+00:00')")
        for ident, outcome, stamp, equipment in [
            ('bad','fail','2026-11-24T09:00:00+00:00','fridge'),
            ('good','pass','2026-11-24T11:00:00+00:00','fridge'),
            ('other','pass','2026-11-24T11:00:00+00:00','oven')]:
            self.db.execute('INSERT INTO sop_inspections VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                ('v',ident,'s',1,'worker',equipment,outcome,None,None,None,
                 'deviation' if outcome=='fail' else None,stamp))
        self.db.execute("INSERT INTO sop_corrective_actions VALUES ('v','fix','bad','worker','Adjusted fridge','2026-11-24T10:00:00+00:00')")
    def tearDown(self):
        self.db.close()
    def link(self, **overrides):
        params=dict(venue_id='v',original_inspection_id='bad',corrective_action_id='fix',
                    recheck_inspection_id='good',linked_by='manager')
        params.update(overrides)
        return link_recheck(self.db,**params)
    def test_links_and_preserves_evidence(self):
        self.link()
        self.assertEqual(self.db.execute('SELECT outcome FROM sop_inspections WHERE inspection_id=?',('bad',)).fetchone(),('fail',))
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute('DELETE FROM sop_rechecks')
    def test_cross_venue_rejected(self):
        with self.assertRaises(ValueError): self.link(venue_id='other-venue')
    def test_mismatched_equipment_rejected(self):
        with self.assertRaises(ValueError): self.link(recheck_inspection_id='other')
    def test_duplicate_recheck_rejected(self):
        self.link()
        with self.assertRaises(sqlite3.IntegrityError): self.link()
    def test_missing_action_rejected(self):
        with self.assertRaises(ValueError): self.link(corrective_action_id='missing')

if __name__ == '__main__':
    unittest.main()
