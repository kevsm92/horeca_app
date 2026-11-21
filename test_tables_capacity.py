"""Synthetic regression tests for physical seat inventory changes."""
import sqlite3
import unittest
from tables_foundation import connect, seat
from tables_capacity import set_table_capacity


class CapacityTests(unittest.TestCase):
    def setUp(self):
        self.db = connect()
        self.db.executemany('INSERT INTO physical_tables VALUES (?,?,?)',
                            [('a', 'T1', 4), ('b', 'T1', 8)])

    def tearDown(self):
        self.db.close()

    def test_change_capacity_within_occupancy(self):
        seat(self.db, 's1', 'a', 'T1', 3)
        set_table_capacity(self.db, 'a', 'T1', 3)
        self.assertEqual(self.db.execute("SELECT capacity FROM physical_tables WHERE venue_id='a'").fetchone()[0], 3)

    def test_cannot_shrink_below_active_guests(self):
        seat(self.db, 's1', 'a', 'T1', 3)
        with self.assertRaises(sqlite3.IntegrityError):
            set_table_capacity(self.db, 'a', 'T1', 2)
        self.assertEqual(self.db.execute("SELECT capacity FROM physical_tables WHERE venue_id='a'").fetchone()[0], 4)

    def test_cross_venue_not_modified(self):
        set_table_capacity(self.db, 'a', 'T1', 2)
        self.assertEqual(self.db.execute("SELECT capacity FROM physical_tables WHERE venue_id='b'").fetchone()[0], 8)
        with self.assertRaises(ValueError):
            set_table_capacity(self.db, 'unknown', 'T1', 3)

    def test_reject_invalid_identifiers_and_seats(self):
        for args in [('', 'T1', 2), ('a', '', 2), ('a', 'T1', True),
                     ('a', 'T1', 0), ('a', 'T1', 101), ('a', 'T1', 2.5)]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                set_table_capacity(self.db, *args)


if __name__ == '__main__':
    unittest.main()
