"""2026-11-14 standalone synthetic table resize contract; NOT integrated.

Visual width/depth are integer centimetres and do not determine seating capacity.
Physical seat inventory is upper bound; occupied guests are lower bound.
Optimistic revision is required for every change. Prototype dimensions 40–400 cm
are UX bounds, not legal or physical universal standards.
"""
from dataclasses import dataclass, replace
import unittest


class ResizeRejected(ValueError):
    pass


@dataclass(frozen=True)
class Table:
    venue_id: str
    table_id: str
    width_cm: int
    depth_cm: int
    seats: int
    physical_seat_inventory: int
    seated_guests: int
    revision: int


def resize(table: Table, *, venue_id: str, expected_revision: int,
           width_cm: int, depth_cm: int, seats: int) -> Table:
    if not venue_id or table.venue_id != venue_id:
        raise ResizeRejected('venue mismatch')
    if expected_revision != table.revision:
        raise ResizeRejected('stale revision')
    if any(type(v) is not int for v in (width_cm, depth_cm, seats)):
        raise ResizeRejected('integer dimensions and seats required')
    if not (40 <= width_cm <= 400 and 40 <= depth_cm <= 400):
        raise ResizeRejected('visual dimensions outside prototype bounds')
    if not (0 <= table.seated_guests <= table.seats <= table.physical_seat_inventory):
        raise ResizeRejected('invalid existing occupancy or inventory')
    if not (table.seated_guests <= seats <= table.physical_seat_inventory):
        raise ResizeRejected('seats must fit inventory and current guests')
    return replace(table, width_cm=width_cm, depth_cm=depth_cm,
                   seats=seats, revision=table.revision + 1)


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.table = Table('venue-a', 'table-1', 90, 90, 4, 6, 3, 7)
        self.args = dict(venue_id='venue-a', expected_revision=7,
                         width_cm=120, depth_cm=80, seats=5)

    def test_valid_resize_and_revision(self):
        result = resize(self.table, **self.args)
        self.assertEqual((result.width_cm, result.depth_cm, result.seats, result.revision), (120, 80, 5, 8))
        self.assertEqual(self.table.revision, 7)

    def test_seats_not_inferred_from_visual_area(self):
        result = resize(self.table, **{**self.args, 'width_cm': 400, 'depth_cm': 400, 'seats': 3})
        self.assertEqual(result.seats, 3)

    def test_reject_below_occupancy(self):
        with self.assertRaises(ResizeRejected):
            resize(self.table, **{**self.args, 'seats': 2})

    def test_reject_above_inventory(self):
        with self.assertRaises(ResizeRejected):
            resize(self.table, **{**self.args, 'seats': 7})

    def test_reject_cross_venue(self):
        with self.assertRaises(ResizeRejected):
            resize(self.table, **{**self.args, 'venue_id': 'venue-b'})

    def test_reject_stale_revision(self):
        with self.assertRaises(ResizeRejected):
            resize(self.table, **{**self.args, 'expected_revision': 6})

    def test_reject_bad_dimensions(self):
        for value in (0, 39, 401, 120.5, True):
            with self.subTest(value=value), self.assertRaises(ResizeRejected):
                resize(self.table, **{**self.args, 'width_cm': value})

    def test_reject_non_integer_seats(self):
        with self.assertRaises(ResizeRejected):
            resize(self.table, **{**self.args, 'seats': 4.5})

    def test_reject_corrupt_existing_state(self):
        with self.assertRaises(ResizeRejected):
            resize(replace(self.table, seated_guests=5), **self.args)


if __name__ == '__main__':
    unittest.main()
