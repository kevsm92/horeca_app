"""Synthetic offline regression tests for transactional waitlist promotion."""
import os
import sqlite3
import tempfile
import threading
import unittest
from reservation_waitlist_promotion import initialize_promotion_fixture, promote, PromotionConflict

T = "2026-11-17T18:00:00+00:00"

class PromotionTests(unittest.TestCase):
    def setUp(self):
        f = tempfile.NamedTemporaryFile(delete=False)
        self.path = f.name
        f.close()
        self.db = self.connection()
        initialize_promotion_fixture(self.db)
        self.db.execute("INSERT INTO promotion_tables VALUES('a','t1',4)")
        self.db.execute("INSERT INTO promotion_tables VALUES('b','t1',4)")
        for venue,request in [('a','w1'),('a','w2'),('b','w1')]:
            self.db.execute(
                "INSERT INTO promotion_waitlist(venue_id,request_id,party_size,start_utc) VALUES(?,?,?,?)",
                (venue,request,2,T))
        self.db.commit()

    def tearDown(self):
        self.db.close()
        os.unlink(self.path)

    def connection(self):
        return sqlite3.connect(self.path,timeout=5,isolation_level=None)

    def call(self,**overrides):
        args=dict(venue_id='a',request_id='w1',table_id='t1',
                  booking_id='bk1',duration_minutes=90,turnover_minutes=15)
        args.update(overrides)
        return promote(self.db,**args)

    def test_success_and_exact_replay(self):
        self.assertTrue(self.call())
        self.assertFalse(self.call())
        self.assertEqual(self.db.execute(
            "SELECT status FROM promotion_waitlist WHERE venue_id='a' AND request_id='w1'"
        ).fetchone()[0],'promoted')

    def test_overlap_rolls_back(self):
        self.call()
        with self.assertRaises(PromotionConflict):
            self.call(request_id='w2',booking_id='bk2')
        self.assertEqual(self.db.execute(
            "SELECT status FROM promotion_waitlist WHERE venue_id='a' AND request_id='w2'"
        ).fetchone()[0],'waiting')

    def test_cross_venue_table_rejected(self):
        with self.assertRaises(PromotionConflict):
            self.call(table_id='other')
        self.assertTrue(self.call(venue_id='b'))

    def test_capacity_and_active_seating(self):
        self.db.execute("UPDATE promotion_tables SET capacity=1 WHERE venue_id='a'")
        with self.assertRaises(PromotionConflict):
            self.call()
        self.db.execute("UPDATE promotion_tables SET capacity=4 WHERE venue_id='a'")
        self.db.execute("INSERT INTO promotion_seating VALUES('a','t1',NULL)")
        with self.assertRaises(PromotionConflict):
            self.call()

    def test_stale_and_identifier_collision(self):
        self.call()
        with self.assertRaises(PromotionConflict):
            self.call(request_id='w2')
        with self.assertRaises(PromotionConflict):
            self.call(booking_id='bk2')

    def test_invalid_input(self):
        with self.assertRaises(ValueError):
            self.call(duration_minutes=True)
        with self.assertRaises(ValueError):
            self.call(venue_id='')

    def test_concurrent_writers_only_one_wins(self):
        barrier=threading.Barrier(2)
        results=[]
        def worker(request,booking):
            db=self.connection()
            try:
                barrier.wait()
                try:
                    results.append(promote(db,venue_id='a',request_id=request,
                                          table_id='t1',booking_id=booking,
                                          duration_minutes=90))
                except PromotionConflict:
                    results.append('conflict')
            finally:
                db.close()
        threads=[threading.Thread(target=worker,args=('w1','bk1')),
                 threading.Thread(target=worker,args=('w2','bk2'))]
        for t in threads: t.start()
        for t in threads: t.join()
        self.assertCountEqual(results,[True,'conflict'])
        self.assertEqual(self.db.execute(
            "SELECT count(*) FROM promotion_bookings WHERE venue_id='a'"
        ).fetchone()[0],1)

if __name__=='__main__':
    unittest.main()
