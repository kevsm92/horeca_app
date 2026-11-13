"""Synthetic venue isolation and input validation for physical table registration."""
import sqlite3
import unittest
from tables_foundation import connect
from tables_inventory import register_physical_table, list_venue_physical_tables


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

    def test_inventory_read_is_venue_scoped_and_does_not_modify_it(self):
        register_physical_table(self.db, 'v1', 'T2', 4)
        register_physical_table(self.db, 'v1', 'T1', 2)
        register_physical_table(self.db, 'v2', 'T1', 6)
        self.assertEqual(list_venue_physical_tables(self.db, 'v1'), [
            {'id': 'T1', 'seats': 2}, {'id': 'T2', 'seats': 4}
        ])
        self.assertEqual(list_venue_physical_tables(self.db, 'v2'), [
            {'id': 'T1', 'seats': 6}
        ])
        self.assertEqual(list_venue_physical_tables(self.db, 'missing'), [])
        self.assertEqual(self.db.execute(
            'SELECT COUNT(*) FROM physical_tables'
        ).fetchone()[0], 3)

    def test_inventory_read_rejects_invalid_venue(self):
        for venue in (None, '', '  ', ' v1', 'v1 ', 123):
            with self.subTest(venue=venue), self.assertRaises(ValueError):
                list_venue_physical_tables(self.db, venue)

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
