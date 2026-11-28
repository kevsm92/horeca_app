import sqlite3
import unittest
from backend.sop_inspections import initialize, record_check, list_checks
from backend.sop_revisions import approve_revision

class Tests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(':memory:')
        initialize(self.db)
        approve_revision(self.db, venue_id='v1', sop_id='cold', author_id='author', approver_id='manager', station='cold', content='Synthetic SOP', expected_previous_revision=0)
        self.db.commit()
    def record(self,**kw):
        args=dict(venue_id='v1',sop_id='cold',revision=1,actor_id='fictional',equipment_id='fridge',outcome='pass')
        args.update(kw)
        return record_check(self.db,**args)
    def test_pass_and_measurement(self):
        self.record(measured_value='4',measured_unit='C',instrument_id='probe')
        row=list_checks(self.db,venue_id='v1',sop_id='cold')[0]
        self.assertEqual(row[4:8],('pass','4','C','probe'))
        self.assertTrue(row[-1].endswith('+00:00'))
    def test_failure_and_recheck_preserved(self):
        self.record(outcome='fail',exception_note='Synthetic deviation')
        self.record()
        self.assertEqual([r[4] for r in list_checks(self.db,venue_id='v1',sop_id='cold')],['fail','pass'])
    def test_incomplete_rejected(self):
        with self.assertRaises(ValueError): self.record(outcome='not_performed')
        with self.assertRaises(ValueError): self.record(measured_value='4')
    def test_tenant_fk_and_scoped_read(self):
        with self.assertRaises(sqlite3.IntegrityError): self.record(venue_id='v2')
        self.record()
        self.assertEqual(list_checks(self.db,venue_id='v2',sop_id='cold'),[])
    def test_immutable(self):
        key=self.record()
        with self.assertRaises(sqlite3.IntegrityError): self.db.execute('UPDATE sop_inspections SET outcome="fail" WHERE inspection_id=?',(key,))
        with self.assertRaises(sqlite3.IntegrityError): self.db.execute('DELETE FROM sop_inspections WHERE inspection_id=?',(key,))

if __name__=='__main__': unittest.main()
