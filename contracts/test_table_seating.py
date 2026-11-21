"""Standalone venue-scoped table seating contract (synthetic; no API integration).

Run: python -m unittest discover -s contracts -p 'test_*.py'
Production must enforce these checks inside a transaction with unique active
(venue_id, table_id) and (venue_id, booking_id) constraints.
"""
from dataclasses import dataclass
import unittest


@dataclass(frozen=True)
class Table:
    venue_id: str
    table_id: str
    physical_seats: int
    enabled: bool = True

    def __post_init__(self):
        if not self.venue_id or not self.table_id or type(self.physical_seats) is not int or self.physical_seats < 1:
            raise ValueError("invalid table inventory")


@dataclass(frozen=True)
class Session:
    venue_id: str
    table_id: str
    booking_id: str
    guests: int
    active: bool = True


def seat(table: Table, booking_id: str, guests: int, sessions: tuple[Session, ...]) -> Session:
    if not isinstance(booking_id, str) or not booking_id:
        raise ValueError("booking required")
    if type(guests) is not int or guests < 1 or guests > table.physical_seats or not table.enabled:
        raise ValueError("invalid occupancy or disabled table")
    for existing in sessions:
        if existing.active and existing.venue_id == table.venue_id:
            if existing.table_id == table.table_id or existing.booking_id == booking_id:
                raise ValueError("double seating")
    return Session(table.venue_id, table.table_id, booking_id, guests)


class TableContractTests(unittest.TestCase):
    def setUp(self):
        self.table = Table("venue-a", "T1", 4)

    def test_valid_assignment(self):
        self.assertEqual(seat(self.table, "B1", 4, ()).guests, 4)

    def test_capacity_and_invalid_guest_counts(self):
        for guests in (0, -1, 5, True, 1.5):
            with self.subTest(guests=guests), self.assertRaises(ValueError):
                seat(self.table, "B1", guests, ())

    def test_active_table_conflict(self):
        with self.assertRaises(ValueError):
            seat(self.table, "B2", 2, (Session("venue-a", "T1", "B1", 2),))

    def test_active_booking_conflict(self):
        with self.assertRaises(ValueError):
            seat(self.table, "B1", 2, (Session("venue-a", "T2", "B1", 2),))

    def test_venue_isolation(self):
        result = seat(self.table, "B1", 2, (Session("venue-b", "T1", "B1", 2),))
        self.assertEqual(result.venue_id, "venue-a")

    def test_closed_session_does_not_block(self):
        self.assertEqual(seat(self.table, "B2", 2, (Session("venue-a", "T1", "B1", 2, False),)).booking_id, "B2")

    def test_disabled_table(self):
        with self.assertRaises(ValueError):
            seat(Table("venue-a", "T1", 4, False), "B1", 2, ())

    def test_invalid_physical_inventory(self):
        for seats in (0, -1, True, 1.5):
            with self.subTest(seats=seats), self.assertRaises(ValueError):
                Table("venue-a", "T1", seats)

    def test_missing_booking(self):
        with self.assertRaises(ValueError):
            seat(self.table, "", 2, ())


if __name__ == "__main__":
    unittest.main()
