"""Regression boundary tests for offline resize preflight (synthetic values only).

Preflight is not authorization or a concurrency-safe database mutation.
"""
import unittest
from table_resize_preflight import validate_table_resize


class ResizePreflightBoundaryTests(unittest.TestCase):
    def test_zero_occupancy_allows_one_seat(self):
        self.assertEqual(validate_table_resize(30, 500, 1, 4, 0),
                         {'width_cm': '30.0', 'depth_cm': '500.0', 'seats': 1})

    def test_equal_active_guests_allowed(self):
        self.assertEqual(validate_table_resize(120.5, 80, 4, 6, 4)['seats'], 4)

    def test_full_table_cannot_shrink(self):
        with self.assertRaises(ValueError):
            validate_table_resize(120, 80, 3, 4, 4)

    def test_inconsistent_snapshot_rejected(self):
        with self.assertRaises(ValueError):
            validate_table_resize(120, 80, 5, 4, 5)

    def test_boolean_and_fractional_seat_values_rejected(self):
        for proposed in (True, False, 2.0, 2.5, '2', None):
            with self.subTest(proposed=proposed), self.assertRaises(ValueError):
                validate_table_resize(120, 80, proposed, 4, 1)

    def test_no_mutation_of_input_or_implicit_inventory_increase(self):
        result = validate_table_resize(120, 80, 3, 4, 1)
        self.assertEqual(set(result), {'width_cm', 'depth_cm', 'seats'})
        with self.assertRaises(ValueError):
            validate_table_resize(120, 80, 5, 4, 1)


if __name__ == '__main__':
    unittest.main()
