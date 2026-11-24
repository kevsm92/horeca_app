import sqlite3
import unittest
from backend.sop_verifications import initialize, verify_recheck


class VerificationTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(':memory:')
        initialize(self.db)
        self.db.execute("INSERT INTO sop_revisions VALUES (?,?,?,?,?,?,?,?,?)",('v','s',1,'author','approver','fridge','synthetic','hash','2026-01-01'))
        for key,actor,outcome in [('original','worker','fail'),('repeat','checker','pass'),('failed_repeat','checker','fail')]:
            self.db.execute("INSERT INTO sop_inspections VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",('v',key,'s',1,actor,'fridge-1',outcome,None,None,None,'synthetic exception' if outcome=='fail' else None,'2026-01-02'))
        self.db.execute("INSERT INTO sop_corrective_actions VALUES (?,?,?,?,?,?)",('v','action','original','worker','synthetic fix','2026-01-03'))
        for key,inspection in [('recheck','repeat'),('bad_recheck','failed_repeat')]:
            self.db.execute("INSERT INTO sop_rechecks VALUES (?,?,?,?,?,?,?)",('v',key,'original','action',inspection,'linker','2026-01-04'))
        self.db.commit()

    def test_invalid_venue(self):
        with self.assertRaises(ValueError):
            verify_recheck(self.db,venue_id='other',recheck_id='recheck',manager_id='mgr',decision='verified',note='reviewed')

    def test_invalid_decision(self):
        with self.assertRaises(ValueError):
            verify_recheck(self.db,venue_id='v',recheck_id='recheck',manager_id='mgr',decision='pass',note='reviewed')

    def test_verification_and_immutability(self):
        key=verify_recheck(self.db,venue_id='v',recheck_id='recheck',manager_id='manager',decision='verified',note='Reviewed synthetic evidence')
        self.assertTrue(key)
        with self.assertRaises(sqlite3.IntegrityError):
            verify_recheck(self.db,venue_id='v',recheck_id='recheck',manager_id='other_manager',decision='verified',note='duplicate')
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("UPDATE sop_manager_verifications SET note='tamper'")
        self.assertEqual(self.db.execute("SELECT outcome FROM sop_inspections WHERE inspection_id='original'").fetchone()[0],'fail')

    def test_reject_failed_recheck_and_self_review(self):
        for recheck,manager in [('bad_recheck','manager'),('recheck','checker'),('recheck','linker')]:
            with self.assertRaises(ValueError):
                verify_recheck(self.db,venue_id='v',recheck_id=recheck,manager_id=manager,decision='verified',note='review')
        verify_recheck(self.db,venue_id='v',recheck_id='bad_recheck',manager_id='manager',decision='rejected',note='Still failed')


if __name__ == '__main__':
    unittest.main()
