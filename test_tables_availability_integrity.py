"""Synthetic corruption tests: availability must never mask broken seating."""
import sqlite3
import unittest
from tables_availability import list_table_availability


class AvailabilityIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.executescript("""
            CREATE TABLE physical_tables (venue_id TEXT, table_id TEXT, capacity INTEGER);
            CREATE TABLE seating_sessions (session_id TEXT, venue_id TEXT,
                table_id TEXT, guest_count INTEGER, status TEXT);
            INSERT INTO physical_tables VALUES ('v1','A',4);
            INSERT INTO physical_tables VALUES ('v2','A',8);
        """)

    def tearDown(self):
        self.db.close()

    def test_valid_projection(self):
        self.db.execute("INSERT INTO seating_sessions VALUES ('s1','v1','A',2,'active')")
        self.assertEqual(list_table_availability(self.db, 'v1'),
                         [('A', 4, 2, 2, 'occupied')])
        self.assertEqual(list_table_availability(self.db, 'v2'),
                         [('A', 8, 0, 8, 'vacant')])

    def test_orphan_active_session_fails_closed(self):
        self.db.execute("INSERT INTO seating_sessions VALUES ('s1','v1','missing',2,'active')")
        with self.assertRaises(ValueError):
            list_table_availability(self.db, 'v1')

    def test_duplicate_active_session_fails_closed(self):
        self.db.executemany('INSERT INTO seating_sessions VALUES (?,?,?,?,?)',
                            [('s1','v1','A',1,'active'), ('s2','v1','A',2,'active')])
        with self.assertRaises(ValueError):
            list_table_availability(self.db, 'v1')

    def test_invalid_active_guests_fail_closed(self):
        for guests in (0, 5, None, 'invalid'):
            with self.subTest(guests=guests):
                self.db.execute('DELETE FROM seating_sessions')
                self.db.execute('INSERT INTO seating_sessions VALUES (?,?,?,?,?)',
                                ('s1','v1','A',guests,'active'))
                with self.assertRaises(ValueError):
                    list_table_availability(self.db, 'v1')


if __name__ == '__main__':
    unittest.main()
