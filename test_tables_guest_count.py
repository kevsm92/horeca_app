import sqlite3
import unittest
from tables_foundation import connect, seat, close
from tables_guest_count import set_active_guest_count


class GuestCountTests(unittest.TestCase):
    def setUp(self):
        self.db = connect()
        self.db.executemany('INSERT INTO physical_tables VALUES (?,?,?)',
                            [('v1', 't1', 4), ('v2', 't1', 3)])
        seat(self.db, 's1', 'v1', 't1', 2)

    def tearDown(self):
        self.db.close()

    def test_increase_and_decrease(self):
        set_active_guest_count(self.db, 'v1', 's1', 4)
        set_active_guest_count(self.db, 'v1', 's1', 1)
        self.assertEqual(self.db.execute("SELECT guest_count FROM seating_sessions WHERE session_id='s1'").fetchone(), (1,))

    def test_capacity_enforced_and_original_unchanged(self):
        with self.assertRaises(sqlite3.IntegrityError):
            set_active_guest_count(self.db, 'v1', 's1', 5)
        self.assertEqual(self.db.execute("SELECT guest_count FROM seating_sessions WHERE session_id='s1'").fetchone(), (2,))

    def test_other_venue_denied(self):
        with self.assertRaises(ValueError):
            set_active_guest_count(self.db, 'v2', 's1', 1)

    def test_closed_session_denied(self):
        close(self.db, 's1', 'v1')
        with self.assertRaises(ValueError):
            set_active_guest_count(self.db, 'v1', 's1', 1)

    def test_invalid_input(self):
        for guests in (0, -1, True, 1.5, '2', None):
            with self.subTest(guests=guests), self.assertRaises(ValueError):
                set_active_guest_count(self.db, 'v1', 's1', guests)
        for venue, session in (('', 's1'), ('v1', ''), (None, 's1'), ('v1', None)):
            with self.assertRaises(ValueError):
                set_active_guest_count(self.db, venue, session, 1)


if __name__ == '__main__':
    unittest.main()
