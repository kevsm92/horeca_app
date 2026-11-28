import sys
import types
import unittest
from unittest.mock import Mock

# Isolated projection tests: real repository dependencies are not locally mounted.
nav = types.ModuleType('tables_navigation')
nav.tables_tab_model = Mock()
sys.modules['tables_navigation'] = nav
from tables_floorplan import floorplan_preview


class FloorplanPreviewTests(unittest.TestCase):
    def setUp(self):
        nav.tables_tab_model.reset_mock()
        nav.tables_tab_model.side_effect = lambda db, venue: {
            'tab': 'Tables', 'venue_id': venue,
            'tables': ([{'table_id': '01', 'status': 'available', 'can_seat': True,
                         'guest_count': 0},
                        {'table_id': '02', 'status': 'occupied', 'can_seat': False,
                         'guest_count': 3},
                        {'table_id': '03', 'status': 'available', 'can_seat': True,
                         'guest_count': 0}] if venue == 'A' else
                       [{'table_id': '99', 'status': 'available', 'can_seat': True,
                         'guest_count': 0}])}

    def test_grid_and_occupancy(self):
        result = floorplan_preview(None, 'A', columns=2)
        self.assertEqual([(t['x'], t['y']) for t in result['tiles']],
                         [(0, 0), (1, 0), (0, 1)])
        self.assertEqual([t['can_seat'] for t in result['tiles']], [True, False, True])
        self.assertEqual(result['tiles'][1]['guest_count'], 3)
        self.assertTrue(all(not t['position_saved'] for t in result['tiles']))

    def test_venue_argument_forwarded(self):
        self.assertEqual([t['table_id'] for t in floorplan_preview(None, 'B')['tiles']], ['99'])
        nav.tables_tab_model.assert_called_once_with(None, 'B')

    def test_invalid_columns_fail_closed(self):
        for value in (0, 13, True, 1.5, '2', None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                floorplan_preview(None, 'A', value)
        nav.tables_tab_model.assert_not_called()

    def test_stable_projection(self):
        self.assertEqual(floorplan_preview(None, 'A'), floorplan_preview(None, 'A'))


if __name__ == '__main__':
    unittest.main()
