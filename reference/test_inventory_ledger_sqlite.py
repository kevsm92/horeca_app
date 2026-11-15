"""Synthetic regression tests: python -m unittest discover -s reference -p 'test_*.py'"""
import os
import sqlite3
import tempfile
import threading
import unittest
from inventory_ledger_sqlite import connect, add_ingredient, append_event, balance, milli

class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name,"ledger.db")
        self.db = connect(self.path)
        add_ingredient(self.db,"v1","flour","g")
        add_ingredient(self.db,"v2","flour","g")
    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()
    def test_venue_isolation(self):
        append_event(self.db,"v1","flour","open",2,"opening")
        self.assertEqual(balance(self.db,"v2","flour"),0)
        with self.assertRaises(ValueError):
            append_event(self.db,"v2","other","x",1,"opening")
    def test_idempotency(self):
        self.assertEqual(append_event(self.db,"v1","flour","a",1,"opening"),1000)
        self.assertEqual(append_event(self.db,"v1","flour","a",1,"opening"),1000)
        self.assertEqual(self.db.execute("SELECT count(*) FROM stock_events").fetchone()[0],1)
    def test_replay_mismatch(self):
        append_event(self.db,"v1","flour","a",1,"opening")
        with self.assertRaises(ValueError):
            append_event(self.db,"v1","flour","a",2,"opening")
    def test_insufficient_rollback(self):
        with self.assertRaises(ValueError):
            append_event(self.db,"v1","flour","a",-1,"consume_mock")
        self.assertEqual(balance(self.db,"v1","flour"),0)
    def test_append_only(self):
        append_event(self.db,"v1","flour","a",1,"opening")
        for sql in ("DELETE FROM stock_events", "UPDATE stock_events SET delta_milli=5"):
            with self.assertRaises(sqlite3.IntegrityError):
                self.db.execute(sql)
    def test_precision(self):
        for value in ("0.0001","NaN","Infinity",0,"10000000000"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                milli(value)
    def test_invalid_reason(self):
        with self.assertRaises(ValueError):
            append_event(self.db,"v1","flour","a",1,"actual_purchase")
    def test_concurrent_last_unit(self):
        append_event(self.db,"v1","flour","seed",1,"opening")
        results=[]
        gate=threading.Barrier(2)
        def consume(i):
            db=connect(self.path)
            gate.wait()
            try:
                append_event(db,"v1","flour",str(i),-1,"consume_mock")
                results.append("ok")
            except ValueError:
                results.append("rejected")
            finally:
                db.close()
        threads=[threading.Thread(target=consume,args=(i,)) for i in range(2)]
        for t in threads:t.start()
        for t in threads:t.join()
        self.assertCountEqual(results,["ok","rejected"])
        self.assertEqual(balance(self.db,"v1","flour"),0)

if __name__=="__main__":
    unittest.main()
