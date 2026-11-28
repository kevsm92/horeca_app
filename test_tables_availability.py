"""Synthetic table availability read-model regressions."""
import unittest

from tables_foundation import connect, seat, close
from tables_availability import list_table_availability


class AvailabilityTests(unittest.TestCase):
    def setUp(self):
        self.db = connect()
        self.db.executemany('INSERT INTO physical_tables VALUES (?,?,?)',
                            [('v1', 'A', 4), ('v1', 'B', 2), ('v2', 'A', 8)])

    def tearDown(self):
        self.db.close()

    def test_vacant_inventory_is_venue_scoped(self):
        self.assertEqual(list_table_availability(self.db, 'v1'),
                         [('A', 4, 0, 4, 'vacant'), ('B', 2, 0, 2, 'vacant')])

    def test_active_session_marks_table_occupied_even_with_spare_seats(self):
        seat(self.db, 's1', 'v1', 'A', 2)
        self.assertEqual(list_table_availability(self.db, 'v1')[0],
                         ('A', 4, 2, 2, 'occupied'))
        self.assertEqual(list_table_availability(self.db, 'v2'),
                         [('A', 8, 0, 8, 'vacant')])

    def test_closed_session_restores_vacancy(self):
        seat(self.db, 's1', 'v1', 'A', 4)
        close(self.db, 's1', 'v1')
        self.assertEqual(list_table_availability(self.db, 'v1')[0],
                         ('A', 4, 0, 4, 'vacant'))

    def test_invalid_venue_rejected(self):
        for value in (None, '', '  ', 5):
            with self.subTest(value=value), self.assertRaises(ValueError):
                list_table_availability(self.db, value)


if __name__ == '__main__':
    unittest.main()
