"""Synthetic venue isolation and input validation for physical table registration."""
import sqlite3
import unittest
from tables_foundation import connect
from tables_inventory import register_physical_table


class TableRegistrationTests(unittest.TestCase):
    def setUp(self):
        self.db = connect()

    def tearDown(self):
        self.db.close()

    def test_same_label_in_two_venues_is_distinct_inventory(self):
        register_physical_table(self.db, 'v1', 'T1', 2)
        register_physical_table(self.db, 'v2', 'T1', 6)
        self.assertEqual(self.db.execute(
            'SELECT venue_id,capacity FROM physical_tables ORDER BY venue_id'
        ).fetchall(), [('v1', 2), ('v2', 6)])

    def test_duplicate_registration_cannot_overwrite_capacity(self):
        register_physical_table(self.db, 'v1', 'T1', 4)
        with self.assertRaises(sqlite3.IntegrityError):
            register_physical_table(self.db, 'v1', 'T1', 8)
        self.assertEqual(self.db.execute(
            'SELECT capacity FROM physical_tables WHERE venue_id=? AND table_id=?',
            ('v1', 'T1')).fetchone()[0], 4)

    def test_reject_invalid_identifiers_and_capacities_without_writes(self):
        bad = [(' ', 'T1', 2), ('v1 ', 'T1', 2), ('v1', '', 2),
               ('v1', ' T1', 2), (None, 'T1', 2), ('v1', 'T1', True),
               ('v1', 'T1', 0), ('v1', 'T1', 101), ('v1', 'T1', 2.0)]
        for args in bad:
            with self.subTest(args=args), self.assertRaises(ValueError):
                register_physical_table(self.db, *args)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM physical_tables').fetchone()[0], 0)


if __name__ == '__main__':
    unittest.main()
