import sqlite3
import unittest
from datetime import datetime, timedelta, timezone
from workflow_outbox import initialize, enqueue, dispatch_mock

NOW = datetime(2026,11,25,tzinfo=timezone.utc)

class OutboxTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        initialize(self.db)

    def test_dedupe_and_venue_isolation(self):
        self.assertTrue(enqueue(self.db,'a','k','task.created',{'task':'synthetic'},NOW))
        self.assertFalse(enqueue(self.db,'a','k','task.created',{'task':'synthetic'},NOW))
        self.assertTrue(enqueue(self.db,'b','k','task.created',{},NOW))
        seen=[]
        self.assertEqual(dispatch_mock(self.db,'a',NOW,lambda typ,p: seen.append(typ)),1)
        self.assertEqual(seen,['task.created'])
        self.assertEqual(self.db.execute("SELECT status FROM workflow_outbox WHERE venue_id='b'").fetchone()[0],'pending')

    def test_conflicting_idempotency_key_rejected(self):
        enqueue(self.db,'a','k','task.created',{'task':'first'},NOW)
        with self.assertRaises(ValueError):
            enqueue(self.db,'a','k','task.created',{'task':'changed'},NOW)
        with self.assertRaises(ValueError):
            enqueue(self.db,'a','k','task.updated',{'task':'first'},NOW)
        self.assertEqual(self.db.execute(
            "SELECT count(*) FROM workflow_outbox WHERE venue_id='a'").fetchone()[0],1)

    def test_retry_dead_letter_and_no_premature_retry(self):
        enqueue(self.db,'a','k','task.created',{},NOW)
        def fail(*args): raise RuntimeError('offline mock failure')
        self.assertEqual(dispatch_mock(self.db,'a',NOW,fail,max_attempts=2),0)
        self.assertEqual(dispatch_mock(self.db,'a',NOW,fail,max_attempts=2),0)
        self.assertEqual(dispatch_mock(self.db,'a',NOW+timedelta(seconds=3),fail,max_attempts=2),0)
        self.assertEqual(self.db.execute('SELECT status,attempts FROM workflow_outbox').fetchone(),('dead',2))

    def test_rollback_with_domain_write(self):
        self.db.execute('CREATE TABLE domain_task(id INTEGER PRIMARY KEY)')
        self.db.commit()
        with self.assertRaises(RuntimeError):
            with self.db:
                self.db.execute('INSERT INTO domain_task VALUES(1)')
                enqueue(self.db,'a','k','task.created',{},NOW)
                raise RuntimeError('rollback')
        self.assertEqual(self.db.execute('SELECT count(*) FROM domain_task').fetchone()[0],0)
        self.assertEqual(self.db.execute('SELECT count(*) FROM workflow_outbox').fetchone()[0],0)

    def test_naive_time_rejected(self):
        with self.assertRaises(ValueError):
            enqueue(self.db,'a','k','event',{},datetime(2026,11,25))

if __name__=='__main__': unittest.main()
