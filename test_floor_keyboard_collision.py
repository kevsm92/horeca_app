"""Synthetic, offline keyboard movement regression cases."""
import unittest
from floor_keyboard_collision import move_table_by_key


class KeyboardCollisionTests(unittest.TestCase):
    def setUp(self):
        self.layout = [('T1', 0, 0, 100, 100), ('T2', 200, 0, 100, 100)]

    def move(self, key='ArrowRight', **kwargs):
        return move_table_by_key(self.layout, 'T1', 400, 300, key, **kwargs)

    def test_moves_one_step_without_mutating_input(self):
        result = self.move()
        self.assertEqual(result[0], ('T1', 50, 0, 100, 100))
        self.assertEqual(self.layout[0], ('T1', 0, 0, 100, 100))

    def test_collision_rejected_without_partial_move(self):
        with self.assertRaisesRegex(ValueError, 'overlapping'):
            self.move(shift=True)
        self.assertEqual(self.layout[0][1], 0)

    def test_edge_noop_and_touching_edges(self):
        self.assertEqual(self.move('ArrowLeft')[0][1], 0)
        self.assertEqual(self.move(shift=False)[0][1], 50)

    def test_missing_table_and_invalid_key(self):
        with self.assertRaises(ValueError):
            move_table_by_key(self.layout, 'missing', 400, 300, 'ArrowRight')
        with self.assertRaises(ValueError):
            self.move('Space')

    def test_invalid_existing_geometry_rejected(self):
        with self.assertRaises(ValueError):
            move_table_by_key([('T1', 350, 0, 100, 100)], 'T1', 400, 300, 'ArrowLeft')

    def test_invalid_bool_step_rejected(self):
        with self.assertRaises(ValueError):
            self.move(step_mm=True)


if __name__ == '__main__':
    unittest.main()
