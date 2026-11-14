"""Synthetic boundary regressions for offline table dimension and seat guards."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'prototypes'))
from table_dimensions import resize_table


class TableDimensionBoundaries(unittest.TestCase):
    def test_inclusive_visual_boundaries(self):
        self.assertEqual(resize_table(40, 500, 2, 2, 500, 40, 2, 2), (500, 40, 2))

    def test_geometry_does_not_increase_seat_inventory(self):
        with self.assertRaisesRegex(ValueError, 'physical inventory'):
            resize_table(100, 100, 2, 0, 500, 500, 3, 2)

    def test_seats_can_equal_active_guests(self):
        self.assertEqual(resize_table(100, 100, 4, 3, 100, 100, 3, 4), (100, 100, 3))

    def test_seats_cannot_drop_below_active_guests(self):
        with self.assertRaisesRegex(ValueError, 'below active guests'):
            resize_table(100, 100, 4, 3, 100, 100, 2, 4)

    def test_invalid_existing_occupancy_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'invalid existing'):
            resize_table(100, 100, 2, 3, 100, 100, 3, 3)

    def test_invalid_existing_inventory_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'invalid existing'):
            resize_table(100, 100, 5, 0, 100, 100, 4, 4)

    def test_noninteger_and_boolean_values_are_rejected(self):
        for value in (True, 2.5, '2', None):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'integer inputs'):
                resize_table(100, 100, 2, 0, 100, 100, value, 4)

    def test_out_of_range_dimensions(self):
        for width, height in ((39, 100), (501, 100), (100, 39), (100, 501)):
            with self.subTest(width=width, height=height), self.assertRaisesRegex(ValueError, 'dimensions'):
                resize_table(100, 100, 2, 0, width, height, 2, 4)

    def test_negative_inventory_and_occupancy(self):
        for seats, guests, limit in ((-1, 0, 4), (2, -1, 4), (2, 0, -1)):
            with self.subTest(seats=seats, guests=guests, limit=limit), self.assertRaisesRegex(ValueError, 'negative'):
                resize_table(100, 100, seats, guests, 100, 100, 2, limit)


if __name__ == '__main__':
    unittest.main()
