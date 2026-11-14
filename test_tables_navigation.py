"""Synthetic offline regression tests for Tables-tab projection."""
import unittest
from tables_foundation import connect, seat, close
from tables_navigation import tables_tab_model


class TablesNavigationTests(unittest.TestCase):
    def setUp(self):
        self.db = connect()
        self.db.execute("INSERT INTO physical_tables VALUES ('v1','A',4)")
        self.db.execute("INSERT INTO physical_tables VALUES ('v1','B',2)")
        self.db.execute("INSERT INTO physical_tables VALUES ('v2','A',6)")

    def tearDown(self):
        self.db.close()

    def test_tab_is_separate_and_venue_scoped(self):
        result = tables_tab_model(self.db, 'v1')
        self.assertEqual(result['tab'], 'Tables')
        self.assertEqual([r['table_id'] for r in result['tables']], ['A', 'B'])
        self.assertTrue(all(r['can_seat'] for r in result['tables']))

    def test_occupied_table_cannot_seat_despite_spare_chairs(self):
        seat(self.db, 's1', 'v1', 'A', 1)
        row = tables_tab_model(self.db, 'v1')['tables'][0]
        self.assertEqual((row['status'], row['guest_count'], row['session_id']), ('occupied', 1, 's1'))
        self.assertFalse(row['can_seat'])
        self.assertIn('1 of 4 seats', row['label'])
        close(self.db, 's1', 'v1')
        self.assertTrue(tables_tab_model(self.db, 'v1')['tables'][0]['can_seat'])

    def test_unknown_venue_empty_and_blank_venue_rejected(self):
        self.assertEqual(tables_tab_model(self.db, 'missing')['tables'], [])
        with self.assertRaises(ValueError):
            tables_tab_model(self.db, '')


if __name__ == '__main__':
    unittest.main()
