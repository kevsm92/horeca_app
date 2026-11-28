"""Synthetic room geometry regression tests; no database or external calls."""
import unittest
from floor_room_bounds import validate_room_footprints


class RoomFootprintTests(unittest.TestCase):
    def test_empty_room_and_edge_touch_are_valid(self):
        self.assertTrue(validate_room_footprints(5000, 3000, []))
        self.assertTrue(validate_room_footprints(5000, 3000, [('T1', 0, 0, 1000, 500), ('T2', 4000, 2500, 1000, 500)]))

    def test_outside_each_boundary_is_rejected(self):
        for footprint in [('T', -1, 0, 1, 1), ('T', 0, -1, 1, 1), ('T', 4999, 0, 2, 1), ('T', 0, 2999, 1, 2)]:
            with self.subTest(footprint=footprint), self.assertRaises(ValueError):
                validate_room_footprints(5000, 3000, [footprint])

    def test_invalid_dimensions_and_boolean_are_rejected(self):
        for dims in [(0, 3000), (5000, -1), (True, 3000), (5000, 3.5)]:
            with self.subTest(dims=dims), self.assertRaises(ValueError):
                validate_room_footprints(*dims, [])
        for item in [('T', 0, 0, True, 1), ('T', 0, 0, 0, 1), ('T', 0, 0, 1.2, 1), ('T', 0, 0, 1, -1)]:
            with self.subTest(item=item), self.assertRaises(ValueError):
                validate_room_footprints(5000, 3000, [item])

    def test_duplicate_and_malformed_records_rejected(self):
        for items in [[('T', 0, 0, 1, 1), ('T', 2, 2, 1, 1)], [('T', 0, 0, 1)], [(' ', 0, 0, 1, 1)], 'invalid', [('T', 0, 0, 1, 1)] * 201]:
            with self.subTest(items=str(items)[:40]), self.assertRaises(ValueError):
                validate_room_footprints(5000, 3000, items)


if __name__ == '__main__':
    unittest.main()
