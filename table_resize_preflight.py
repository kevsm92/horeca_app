"""Offline, pure preflight for editing one venue-owned physical table.

This does not authorize requests, change inventory, or persist floor plans.
The caller must obtain current venue-scoped occupancy in the same transaction
as the eventual capacity update; a database guard must recheck concurrency.
"""
from table_visual_dimensions import validate_visual_dimensions


def validate_table_resize(width_cm, depth_cm, requested_seats, inventory_seats,
                          active_guests):
    """Validate geometry and seat change independently; fail closed on stale counts."""
    dimensions = validate_visual_dimensions(width_cm, depth_cm)
    for name, value in (("requested_seats", requested_seats),
                        ("inventory_seats", inventory_seats),
                        ("active_guests", active_guests)):
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer")
    if not 1 <= inventory_seats <= 100:
        raise ValueError("inventory_seats outside physical table capacity bounds")
    if not 0 <= active_guests <= inventory_seats:
        raise ValueError("active_guests inconsistent with physical inventory")
    if not active_guests <= requested_seats <= inventory_seats:
        raise ValueError("requested seats must fit active guests and physical inventory")
    if requested_seats < 1:
        raise ValueError("requested seats must be positive")
    return {**dimensions, "seats": requested_seats}


if __name__ == "__main__":
    import unittest

    class PreflightTests(unittest.TestCase):
        def test_valid_geometry_and_seats(self):
            self.assertEqual(validate_table_resize(120.5, 80, 3, 4, 2),
                             {"width_cm": "120.5", "depth_cm": "80.0", "seats": 3})

        def test_cannot_exceed_inventory_or_shrink_below_guests(self):
            for seats in (1, 5, 0, -1):
                with self.subTest(seats=seats), self.assertRaises(ValueError):
                    validate_table_resize(120, 80, seats, 4, 2)

        def test_reject_stale_and_invalid_counts(self):
            for args in ((2, 4, 5), (2, 0, 0), (2, 101, 0),
                         (True, 4, 0), (2, 4, False), (2, 4, -1),
                         (2.0, 4, 0), (2, 4.0, 0)):
                with self.subTest(args=args), self.assertRaises(ValueError):
                    validate_table_resize(120, 80, *args)

        def test_invalid_geometry_cannot_be_masked_by_seats(self):
            with self.assertRaises(ValueError):
                validate_table_resize(20, 80, 3, 4, 2)

    unittest.main()
