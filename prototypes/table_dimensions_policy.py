"""Offline HORECA table resize policy prototype; no database or public API.

Visual dimensions never alter physical inventory. Run: python -m unittest
prototypes.table_dimensions_policy -v
"""
from dataclasses import dataclass
import unittest


@dataclass(frozen=True)
class TableState:
    venue_id: str
    table_id: str
    physical_seats: int
    configured_seats: int
    seated_guests: int
    width_cm: int
    depth_cm: int
    revision: int


class ResizeRejected(ValueError):
    pass


def resize_table(table: TableState, *, venue_id: str, expected_revision: int,
                 width_cm: int, depth_cm: int, configured_seats: int) -> TableState:
    """Return immutable revised state; persistence must atomically check revision."""
    if not venue_id or venue_id != table.venue_id:
        raise ResizeRejected("venue mismatch")
    if type(expected_revision) is not int or expected_revision != table.revision:
        raise ResizeRejected("stale revision")
    if not table.table_id or not table.venue_id:
        raise ResizeRejected("invalid table identity")
    if any(type(v) is not int for v in (width_cm, depth_cm, configured_seats)):
        raise ResizeRejected("integer values required")
    if not (40 <= width_cm <= 400 and 40 <= depth_cm <= 400):
        raise ResizeRejected("visual dimensions outside prototype bounds")
    if not (1 <= table.physical_seats <= 30):
        raise ResizeRejected("invalid physical inventory")
    if not (0 <= table.seated_guests <= table.configured_seats <= table.physical_seats):
        raise ResizeRejected("invalid existing occupancy")
    if not (table.seated_guests <= configured_seats <= table.physical_seats):
        raise ResizeRejected("seat count conflicts with occupancy or inventory")
    return TableState(table.venue_id, table.table_id, table.physical_seats,
                      configured_seats, table.seated_guests, width_cm, depth_cm,
                      table.revision + 1)


class ResizePolicyTests(unittest.TestCase):
    def setUp(self):
        self.table = TableState("venue-a", "table-1", 6, 4, 3, 120, 80, 7)

    def change(self, **kwargs):
        args = dict(venue_id="venue-a", expected_revision=7,
                    width_cm=150, depth_cm=90, configured_seats=4)
        args.update(kwargs)
        return resize_table(self.table, **args)

    def test_valid_resize_preserves_inventory_and_occupancy(self):
        result = self.change(configured_seats=6)
        self.assertEqual((result.width_cm, result.depth_cm, result.revision), (150, 90, 8))
        self.assertEqual((result.physical_seats, result.seated_guests), (6, 3))
        self.assertEqual(self.table.revision, 7)

    def test_visual_resize_does_not_increase_seats(self):
        self.assertEqual(self.change(width_cm=400).configured_seats, 4)

    def test_below_occupancy_rejected(self):
        with self.assertRaises(ResizeRejected):
            self.change(configured_seats=2)

    def test_over_inventory_rejected(self):
        with self.assertRaises(ResizeRejected):
            self.change(configured_seats=7)

    def test_cross_venue_rejected(self):
        with self.assertRaises(ResizeRejected):
            self.change(venue_id="venue-b")

    def test_stale_revision_rejected(self):
        with self.assertRaises(ResizeRejected):
            self.change(expected_revision=6)

    def test_non_integer_and_boolean_values_rejected(self):
        for changes in ({"width_cm": 120.5}, {"configured_seats": True},
                        {"expected_revision": True}, {"depth_cm": "90"}):
            with self.subTest(changes=changes), self.assertRaises(ResizeRejected):
                self.change(**changes)

    def test_visual_limits_rejected(self):
        for changes in ({"width_cm": 39}, {"depth_cm": 401}):
            with self.subTest(changes=changes), self.assertRaises(ResizeRejected):
                self.change(**changes)

    def test_invalid_existing_occupancy_rejected(self):
        broken = TableState("venue-a", "table-1", 6, 4, 5, 120, 80, 7)
        with self.assertRaises(ResizeRejected):
            resize_table(broken, venue_id="venue-a", expected_revision=7,
                         width_cm=150, depth_cm=90, configured_seats=6)


if __name__ == "__main__":
    unittest.main()
