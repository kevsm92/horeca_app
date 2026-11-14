import sqlite3
import unittest
from tables_foundation import connect, seat, close

class TablesFoundationTests(unittest.TestCase):
    def setUp(self):
        self.db = connect()
        self.db.executemany('INSERT INTO physical_tables VALUES (?,?,?)',
                            [('v1','t1',4),('v2','t1',2)])
    def tearDown(self):
        self.db.close()
    def test_valid_seating_and_close(self):
        seat(self.db,'s1','v1','t1',4)
        close(self.db,'s1','v1')
        seat(self.db,'s2','v1','t1',1)
    def test_double_seating_blocked(self):
        seat(self.db,'s1','v1','t1',2)
        with self.assertRaises(sqlite3.IntegrityError):
            seat(self.db,'s2','v1','t1',1)
    def test_capacity_blocked(self):
        with self.assertRaises(sqlite3.IntegrityError):
            seat(self.db,'s1','v1','t1',5)
    def test_cross_venue_table_blocked(self):
        with self.assertRaises(sqlite3.IntegrityError):
            seat(self.db,'s1','v1','nonexistent',1)
    def test_venue_isolation(self):
        seat(self.db,'s1','v1','t1',2)
        seat(self.db,'s2','v2','t1',2)
        with self.assertRaises(ValueError):
            close(self.db,'s1','v2')
    def test_cannot_shrink_below_active_occupancy(self):
        seat(self.db,'s1','v1','t1',3)
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("UPDATE physical_tables SET capacity=2 WHERE venue_id='v1' AND table_id='t1'")
    def test_update_cannot_exceed_capacity(self):
        seat(self.db,'s1','v1','t1',2)
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("UPDATE seating_sessions SET guest_count=5 WHERE session_id='s1'")
    def test_invalid_capacity_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO physical_tables VALUES ('v1','bad',0)")

if __name__ == '__main__':
    unittest.main()
