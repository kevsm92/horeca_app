"""Focused synthetic tests: run python -m unittest discover -s prototypes -p 'test_workflow_outbox_claim.py'."""
import sqlite3
import unittest
try:
    from .workflow_outbox_claim import init, enqueue, claim, complete, retry
except ImportError:
    from workflow_outbox_claim import init, enqueue, claim, complete, retry

class OutboxTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(':memory:')
        init(self.db)
    def tearDown(self): self.db.close()
    def test_claim_ack_once(self):
        i=enqueue(self.db,'venue-a','task.created','{"synthetic":true}')
        row=claim(self.db,100)
        self.assertEqual((row[0],row[1],row[4]),(i,'venue-a',1))
        self.assertIsNone(claim(self.db,100))
        self.assertTrue(complete(self.db,i,1))
        self.assertFalse(complete(self.db,i,1))
    def test_lease_fences_stale_worker(self):
        i=enqueue(self.db,'venue-a','task.created','{}')
        self.assertEqual(claim(self.db,100)[4],1)
        self.assertEqual(claim(self.db,131)[4],2)
        self.assertFalse(complete(self.db,i,1))
        self.assertTrue(complete(self.db,i,2))
    def test_retry_respects_due_time(self):
        i=enqueue(self.db,'venue-b','task.created','{}')
        self.assertTrue(retry(self.db,i,claim(self.db,100)[4],150))
        self.assertIsNone(claim(self.db,149))
        self.assertEqual(claim(self.db,150)[0],i)
    def test_rollback_domain_and_outbox(self):
        self.db.execute('BEGIN')
        enqueue(self.db,'venue-a','task.created','{}')
        self.db.rollback()
        self.assertIsNone(claim(self.db,100))
    def test_invalid_json_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            enqueue(self.db,'venue-a','task.created','not json')
if __name__=='__main__': unittest.main()
