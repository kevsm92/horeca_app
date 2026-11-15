"""File-backed SQLite concurrency regressions using synthetic reservations."""
import os
import sqlite3
import tempfile
import threading
import unittest
from reservation_modify_sqlite import ModificationConflict, modify_reservation

class IndependentConnectionModificationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, 'synthetic.sqlite3')
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE tables(venue TEXT,id TEXT,capacity INTEGER,PRIMARY KEY(venue,id));
                CREATE TABLE bookings(venue TEXT,id TEXT,table_id TEXT,party INTEGER,
                    start_us INTEGER,end_us INTEGER,turnover_us INTEGER,status TEXT,
                    revision INTEGER,PRIMARY KEY(venue,id));
                INSERT INTO tables VALUES ('v','t',4),('other','t',4);
                INSERT INTO bookings VALUES ('v','r1','t',2,100,200,10,'confirmed',0),
                    ('v','r2','t',2,300,400,10,'confirmed',0),
                    ('other','r1','t',2,100,200,10,'confirmed',0);
            """)
    def tearDown(self):
        self.tmp.cleanup()
    def connect(self):
        return sqlite3.connect(self.path, timeout=3, isolation_level=None)
    def modify(self, db, booking_id, start_us, end_us, revision=0):
        return modify_reservation(db, venue='v', booking_id=booking_id,
            expected_revision=revision, table_id='t', party=2,
            start_us=start_us, end_us=end_us, turnover_us=10)
    def test_independent_connection_rejects_stale_revision(self):
        with self.connect() as first, self.connect() as second:
            self.assertEqual(self.modify(first, 'r1', 500, 600), 1)
            with self.assertRaises(ModificationConflict):
                self.modify(second, 'r1', 700, 800)
            self.assertEqual(first.execute("SELECT start_us,revision FROM bookings WHERE venue='v' AND id='r1'").fetchone(), (500, 1))
    def test_writer_lock_serializes_competing_modifications(self):
        entered = threading.Event()
        result = []
        with self.connect() as first:
            first.execute('BEGIN IMMEDIATE')
            first.execute("UPDATE bookings SET start_us=500,end_us=600,revision=1 WHERE venue='v' AND id='r1'")
            def contender():
                with self.connect() as second:
                    entered.set()
                    try:
                        result.append(('ok', self.modify(second, 'r1', 700, 800)))
                    except ModificationConflict:
                        result.append(('conflict', None))
                    except Exception as exc:
                        result.append(('error', type(exc).__name__))
            thread = threading.Thread(target=contender)
            thread.start()
            try:
                self.assertTrue(entered.wait(2))
                self.assertEqual(result, [], 'contender should wait for writer lock')
                first.commit()
                thread.join(3)
                self.assertFalse(thread.is_alive())
                self.assertEqual(result, [('conflict', None)])
                self.assertEqual(first.execute("SELECT start_us,revision FROM bookings WHERE venue='v' AND id='r1'").fetchone(), (500, 1))
            finally:
                if first.in_transaction:
                    first.rollback()
                thread.join(3)
    def test_conflict_with_other_booking_rechecked_after_commit(self):
        with self.connect() as first, self.connect() as second:
            self.assertEqual(self.modify(first, 'r1', 500, 600), 1)
            with self.assertRaises(ModificationConflict):
                self.modify(second, 'r2', 605, 700)
            self.assertEqual(second.execute("SELECT start_us,revision FROM bookings WHERE venue='v' AND id='r2'").fetchone(), (300, 0))
            self.assertEqual(second.execute("SELECT start_us,revision FROM bookings WHERE venue='other' AND id='r1'").fetchone(), (100, 0))

if __name__ == '__main__':
    unittest.main()
