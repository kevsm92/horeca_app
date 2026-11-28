"""Synthetic-only tests for the offline purchasing prototype."""
import sqlite3
import unittest
from purchase_requisitions import initialize, create_draft, transition

class PurchaseRequisitionTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(':memory:')
        initialize(self.db)
        create_draft(self.db,venue_id='fictional-a',requisition_id='req-1',
          supplier_id='fictional-supplier',item_name='Synthetic flour',
          quantity=2,unit_price_cents=1500,requested_by='fictional-worker')

    def move(self,action,venue='fictional-a',actor='fictional-worker',role='staff'):
        return transition(self.db,venue_id=venue,requisition_id='req-1',
          actor_id=actor,actor_role=role,action=action)

    def test_separate_manager_approval(self):
        self.assertTrue(self.move('submit'))
        self.assertFalse(self.move('approve'))
        self.assertFalse(self.move('approve',role='manager'))
        self.assertTrue(self.move('approve',actor='fictional-manager',role='manager'))
        self.assertFalse(self.move('approve',actor='fictional-manager',role='manager'))

    def test_cross_venue_isolation(self):
        self.assertFalse(self.move('submit',venue='fictional-b'))
        self.assertEqual(self.db.execute('SELECT status FROM purchase_requisitions').fetchone()[0],'draft')

    def test_rejection_requires_manager(self):
        self.assertTrue(self.move('submit'))
        self.assertFalse(self.move('reject',actor='fictional-peer'))
        self.assertTrue(self.move('reject',actor='fictional-manager',role='manager'))

    def test_invalid_money_and_quantity(self):
        for quantity,cents in [(0,100),(1,-1),(True,100),(1,2.5)]:
            with self.assertRaises(ValueError):
                create_draft(self.db,venue_id='fictional-a',requisition_id='bad',
                  supplier_id='supplier',item_name='item',quantity=quantity,
                  unit_price_cents=cents,requested_by='staff')

    def test_requester_only_submission(self):
        self.assertFalse(self.move('submit',actor='other'))
        self.assertTrue(self.move('submit'))
        self.assertFalse(self.move('submit'))

if __name__=='__main__':
    unittest.main()
