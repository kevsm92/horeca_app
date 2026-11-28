"""Offline optimistic-concurrency gate for a physical table resize.

Call inside an authorized venue-scoped database transaction after locking the
physical table and current seating session. Never trust client-supplied counts.
"""
from table_resize_preflight import validate_table_resize


def validate_resize_revision(width_cm, depth_cm, requested_seats, *,
                             expected_revision, current_revision,
                             physical_seats, seated_guests):
    """Return validated next state; reject stale edits without side effects."""
    for label, value in (("expected_revision", expected_revision),
                         ("current_revision", current_revision)):
        if type(value) is not int or value < 0 or value >= 2**63 - 1:
            raise ValueError(f"{label} must be a nonnegative 63-bit revision")
    if expected_revision != current_revision:
        raise ValueError("stale table revision; reload before resizing")
    resized = validate_table_resize(width_cm, depth_cm, requested_seats,
                                    physical_seats, seated_guests)
    return {**resized, "revision": current_revision + 1}


if __name__ == "__main__":
    import unittest

    class RevisionTests(unittest.TestCase):
        def test_success_increments_once(self):
            self.assertEqual(validate_resize_revision(120, 80, 3,
                expected_revision=7, current_revision=7,
                physical_seats=4, seated_guests=2),
                {"width_cm": "120.0", "depth_cm": "80.0", "seats": 3,
                 "revision": 8})

        def test_stale_and_malformed_revisions(self):
            for expected, current in ((1, 2), (-1, 0), (True, 1),
                                      (1.0, 1), (None, 0), (0, 2**63-1)):
                with self.subTest(expected=expected, current=current):
                    with self.assertRaises(ValueError):
                        validate_resize_revision(120, 80, 3,
                            expected_revision=expected, current_revision=current,
                            physical_seats=4, seated_guests=2)

        def test_rechecks_live_occupancy_and_inventory(self):
            for seats, physical, guests in ((1, 4, 2), (5, 4, 2), (3, 4, 5)):
                with self.subTest(seats=seats, physical=physical, guests=guests):
                    with self.assertRaises(ValueError):
                        validate_resize_revision(120, 80, seats,
                            expected_revision=2, current_revision=2,
                            physical_seats=physical, seated_guests=guests)

    unittest.main()
