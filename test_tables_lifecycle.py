"""Synthetic lifecycle invariants enforced even against direct SQL writes."""
import sqlite3
import unittest
from tables_foundation import connect, seat, close

class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.db = connect()
        self.db.execute("INSERT INTO physical_tables VALUES ('v1','t1',4)")
        self.db.execute("INSERT INTO physical_tables VALUES ('v1','t2',4)")
        seat(self.db, 's1', 'v1', 't1', 2)

    def tearDown(self):
        self.db.close()

    def test_closed_session_cannot_reopen_or_change_guest_count(self):
        close(self.db, 's1', 'v1')
        for sql in ["UPDATE seating_sessions SET status='active' WHERE session_id='s1'",
                    "UPDATE seating_sessions SET guest_count=3 WHERE session_id='s1'"]:
            with self.assertRaises(sqlite3.IntegrityError):
                self.db.execute(sql)
        self.assertEqual(self.db.execute("SELECT status,guest_count FROM seating_sessions WHERE session_id='s1'").fetchone(), ('closed',2))

    def test_identity_and_table_cannot_be_reassigned(self):
        for sql in ["UPDATE seating_sessions SET table_id='t2' WHERE session_id='s1'",
                    "UPDATE seating_sessions SET session_id='other' WHERE session_id='s1'",
                    "UPDATE seating_sessions SET venue_id='v2' WHERE session_id='s1'"]:
            with self.assertRaises(sqlite3.IntegrityError):
                self.db.execute(sql)

    def test_delete_forbidden_and_close_is_one_way(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("DELETE FROM seating_sessions WHERE session_id='s1'")
        close(self.db, 's1', 'v1')
        with self.assertRaises(ValueError):
            close(self.db, 's1', 'v1')
        seat(self.db, 's2', 'v1', 't1', 1)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM seating_sessions").fetchone()[0],2)

if __name__ == '__main__':
    unittest.main()
