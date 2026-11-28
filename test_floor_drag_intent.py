import unittest
from floor_drag_intent import drag_table


class DragIntentTests(unittest.TestCase):
    def setUp(self):
        self.rects = [('a', 0, 0, 100, 100), ('b', 200, 0, 100, 100)]

    def move(self, table='a', x=100, y=100, rects=None, floor=(400, 400)):
        return drag_table(self.rects if rects is None else rects, table, x, y, *floor)

    def test_valid_move_and_immutable_input(self):
        moved = self.move()
        self.assertEqual(moved[0], ('a', 100, 100, 100, 100))
        self.assertEqual(self.rects[0], ('a', 0, 0, 100, 100))

    def test_touching_edges_allowed(self):
        self.assertEqual(self.move(x=100, y=0)[0][1:3], (100, 0))

    def test_overlap_rejected(self):
        with self.assertRaises(ValueError): self.move(x=150, y=0)

    def test_outside_floor_rejected(self):
        with self.assertRaises(ValueError): self.move(x=350, y=0)

    def test_missing_table_rejected(self):
        with self.assertRaises(ValueError): self.move(table='other')

    def test_bool_coordinate_rejected(self):
        with self.assertRaises(ValueError): self.move(x=True)

    def test_existing_outside_floor_rejected(self):
        with self.assertRaises(ValueError): self.move(floor=(250, 400))

    def test_duplicate_table_rejected(self):
        with self.assertRaises(ValueError): self.move(rects=[('a', 0, 0, 100, 100), ('a', 200, 0, 100, 100)])


if __name__ == '__main__':
    unittest.main()
