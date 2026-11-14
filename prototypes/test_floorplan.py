"""Synthetic regression tests for floor-plan coordinate prototype."""
import unittest
from floorplan import LayoutConflict, TablePosition, keyboard_move, move_table

class FloorPlanTests(unittest.TestCase):
    def setUp(self):
        self.p = TablePosition('venue-demo', 'table-01', 20, 30, 4)
        self.args = dict(venue_id='venue-demo', table_id='table-01',
                         expected_revision=4, canvas_width=200, canvas_height=100)

    def test_drag_move_increments_revision(self):
        moved = move_table(self.p, x=40, y=50, **self.args)
        self.assertEqual((moved.x, moved.y, moved.revision), (40, 50, 5))
        self.assertEqual(self.p.revision, 4)

    def test_stale_revision_rejected(self):
        with self.assertRaises(LayoutConflict):
            move_table(self.p, x=40, y=50, **{**self.args, 'expected_revision': 3})

    def test_cross_venue_and_table_rejected(self):
        for field, value in [('venue_id', 'other'), ('table_id', 'other')]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                move_table(self.p, x=40, y=50, **{**self.args, field: value})

    def test_invalid_positions_rejected(self):
        for x, y in [(-1, 0), (200, 0), (0, 100), (True, 0), (0, 1.5)]:
            with self.subTest(x=x, y=y), self.assertRaises(ValueError):
                move_table(self.p, x=x, y=y, **self.args)

    def test_keyboard_move_and_clamp(self):
        moved = keyboard_move(self.p, key='ArrowRight', canvas_width=200, canvas_height=100)
        self.assertEqual((moved.x, moved.revision), (30, 5))
        edge = TablePosition('venue-demo', 'table-01', 0, 0, 4)
        self.assertIs(keyboard_move(edge, key='ArrowLeft', canvas_width=200, canvas_height=100), edge)

    def test_noop_does_not_increment(self):
        self.assertIs(move_table(self.p, x=20, y=30, **self.args), self.p)

    def test_bad_keyboard_input(self):
        with self.assertRaises(ValueError):
            keyboard_move(self.p, key='Enter', canvas_width=200, canvas_height=100)
        with self.assertRaises(ValueError):
            keyboard_move(self.p, key='ArrowUp', step=0, canvas_width=200, canvas_height=100)

if __name__ == '__main__':
    unittest.main()
