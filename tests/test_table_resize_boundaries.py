"""Synthetic edge cases for the pure table resizing contract."""
import unittest
from horeca_tables.dimensions import TableInventory, resize_table


class ResizeBoundaryTests(unittest.TestCase):
    def test_minimum_dimensions_and_seats_for_empty_table(self):
        original = TableInventory('venue-demo', 'T-1', 2, 2, 0, 100, 100, 0)
        updated = resize_table(original, venue_id='venue-demo', expected_revision=0,
                               width_cm=40, depth_cm=40, seats=1)
        self.assertEqual((updated.width_cm, updated.depth_cm, updated.configured_seats), (40, 40, 1))
        self.assertEqual(original.configured_seats, 2)
        self.assertEqual(original.revision, 0)
        self.assertEqual(updated.revision, 1)

    def test_maximum_dimensions_and_full_occupancy(self):
        original = TableInventory('venue-demo', 'T-2', 8, 8, 8, 100, 100, 3)
        updated = resize_table(original, venue_id='venue-demo', expected_revision=3,
                               width_cm=400, depth_cm=400, seats=8)
        self.assertEqual((updated.width_cm, updated.depth_cm, updated.active_guests), (400, 400, 8))
        with self.assertRaises(ValueError):
            resize_table(original, venue_id='venue-demo', expected_revision=3,
                         width_cm=400, depth_cm=400, seats=7)

    def test_boolean_seat_count_and_revision_are_rejected(self):
        original = TableInventory('venue-demo', 'T-3', 4, 4, 0, 100, 100, 1)
        for changes in ({'seats': True}, {'expected_revision': True}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                resize_table(original, **(dict(venue_id='venue-demo', expected_revision=1,
                             width_cm=100, depth_cm=100, seats=2) | changes))


if __name__ == '__main__':
    unittest.main()
