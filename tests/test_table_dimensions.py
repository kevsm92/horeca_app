import unittest
from horeca_tables.dimensions import TableInventory, resize_table


class TableResizeTests(unittest.TestCase):
    def setUp(self):
        self.table = TableInventory('venue-A', 'T1', 6, 6, 4, 100, 80, 7)

    def change(self, **kwargs):
        args = dict(venue_id='venue-A', expected_revision=7, width_cm=120, depth_cm=90, seats=5)
        args.update(kwargs)
        return resize_table(self.table, **args)

    def test_valid_resize_keeps_physical_inventory_and_occupancy(self):
        updated = self.change()
        self.assertEqual((updated.width_cm, updated.depth_cm, updated.revision), (120, 90, 8))
        self.assertEqual((updated.physical_seats, updated.configured_seats, updated.active_guests), (6, 5, 4))

    def test_cannot_reduce_below_seated_guests(self):
        with self.assertRaises(ValueError): self.change(seats=3)

    def test_cannot_exceed_physical_seats(self):
        with self.assertRaises(ValueError): self.change(seats=7)

    def test_rejects_cross_venue(self):
        with self.assertRaises(ValueError): self.change(venue_id='venue-B')

    def test_rejects_stale_revision(self):
        with self.assertRaises(ValueError): self.change(expected_revision=6)

    def test_rejects_invalid_dimensions(self):
        for value in (0, 401, 100.5, True):
            with self.subTest(value=value), self.assertRaises(ValueError): self.change(width_cm=value)

    def test_rejects_corrupt_occupancy(self):
        invalid = TableInventory('venue-A', 'T1', 3, 3, 4, 100, 80, 7)
        with self.assertRaises(ValueError):
            resize_table(invalid, venue_id='venue-A', expected_revision=7, width_cm=120, depth_cm=90, seats=3)


if __name__ == '__main__':
    unittest.main()
