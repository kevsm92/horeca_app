"""Synthetic boundary regression for the pure table dimension policy."""
import unittest
from dataclasses import replace
from horeca_tables.dimensions import TableInventory, resize_table


class TableDimensionBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.table = TableInventory('venue-A', 'table-1', 6, 4, 3, 120, 80, 7)

    def change(self, table=None, **overrides):
        args = dict(venue_id='venue-A', expected_revision=7, width_cm=120,
                    depth_cm=80, seats=4)
        args.update(overrides)
        return resize_table(table or self.table, **args)

    def test_exact_occupancy_boundary_and_immutable_revision(self):
        updated = self.change(seats=3)
        self.assertEqual((updated.configured_seats, updated.revision), (3, 8))
        self.assertEqual((self.table.configured_seats, self.table.revision), (4, 7))

    def test_rejects_boolean_stored_counts_and_revision(self):
        for field in ('physical_seats', 'configured_seats', 'active_guests', 'revision'):
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.change(replace(self.table, **{field: True}))

    def test_rejects_cross_venue_and_stale_revision(self):
        for override in ({'venue_id': 'venue-B'}, {'expected_revision': 6},
                         {'expected_revision': True}):
            with self.subTest(override=override), self.assertRaises(ValueError):
                self.change(**override)

    def test_rejects_oversubscription_and_underoccupancy(self):
        for seats in (2, 7, 0, True, 3.5):
            with self.subTest(seats=seats), self.assertRaises(ValueError):
                self.change(seats=seats)

    def test_dimensions_boundaries(self):
        self.assertEqual(self.change(width_cm=40, depth_cm=400).width_cm, 40)
        for dimension in ('width_cm', 'depth_cm'):
            for value in (39, 401, True, 40.5):
                with self.subTest(dimension=dimension, value=value), self.assertRaises(ValueError):
                    self.change(**{dimension: value})


if __name__ == '__main__':
    unittest.main()
