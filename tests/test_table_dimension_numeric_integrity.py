"""Regression checks for strict numeric state in offline table resizing."""
import unittest
from dataclasses import replace
from horeca_tables.dimensions import TableInventory, resize_table


class NumericIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.table = TableInventory("venue-A", "T1", 6, 5, 3, 100, 80, 7)

    def resize(self, table=None, **kwargs):
        args = dict(venue_id="venue-A", expected_revision=7, width_cm=120, depth_cm=90, seats=5)
        args.update(kwargs)
        return resize_table(table if table is not None else self.table, **args)

    def test_valid(self):
        self.assertEqual(self.resize().revision, 8)

    def test_rejects_noninteger_stored_fields(self):
        for field in ("physical_seats", "configured_seats", "active_guests", "width_cm", "depth_cm", "revision"):
            for value in (True, 3.0, "3"):
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    self.resize(replace(self.table, **{field: value}))

    def test_rejects_boolean_float_or_negative_revision(self):
        for value in (True, 7.0, "7", -1):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.resize(expected_revision=value)

    def test_rejects_zero_configured_seats_even_if_empty(self):
        with self.assertRaises(ValueError):
            self.resize(replace(self.table, configured_seats=0, active_guests=0))

    def test_rejects_occupancy_above_configured_seats(self):
        with self.assertRaises(ValueError):
            self.resize(replace(self.table, configured_seats=2, active_guests=3))

    def test_rejects_zero_requested_seats(self):
        with self.assertRaises(ValueError):
            self.resize(seats=0)


if __name__ == "__main__":
    unittest.main()
