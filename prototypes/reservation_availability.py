"""Offline table-aware reservation availability prototype; no booking writes."""
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass(frozen=True)
class Table:
    venue: str
    id: str
    seats: int

@dataclass(frozen=True)
class Booking:
    venue: str
    table_id: str
    start: datetime
    end: datetime
    status: str = "confirmed"

def available(venue, party, start, end, tables, bookings, turnover_minutes=0):
    """Half-open intervals, symmetric turnover; never authorizes or books a table."""
    def aware(t):
        return isinstance(t, datetime) and t.tzinfo is not None and t.utcoffset() is not None
    if not venue or type(party) is not int or party < 1:
        raise ValueError("invalid venue/party")
    if type(turnover_minutes) is not int or not 0 <= turnover_minutes <= 240:
        raise ValueError("invalid turnover")
    if not aware(start) or not aware(end) or end <= start:
        raise ValueError("invalid interval")
    inventory = {}
    for table in tables:
        if table.venue != venue:
            continue
        if not table.id or type(table.seats) is not int or table.seats < 1 or table.id in inventory:
            raise ValueError("invalid physical inventory")
        inventory[table.id] = table.seats
    blocked = set()
    buffer = timedelta(minutes=turnover_minutes)
    for booking in bookings:
        if booking.venue != venue or booking.status == "cancelled":
            continue
        if booking.status not in ("confirmed", "seated"):
            raise ValueError("unsupported booking status")
        if booking.table_id not in inventory or not aware(booking.start) or not aware(booking.end) or booking.end <= booking.start:
            raise ValueError("invalid stored booking")
        if start < booking.end + buffer and booking.start < end + buffer:
            blocked.add(booking.table_id)
    return sorted(t for t, seats in inventory.items() if seats >= party and t not in blocked)

if __name__ == "__main__":
    import unittest
    from datetime import timezone
    class Tests(unittest.TestCase):
        def setUp(self):
            self.t = datetime(2026, 11, 15, 18, tzinfo=timezone.utc)
            self.tables = [Table("a", "small", 2), Table("a", "large", 4), Table("b", "foreign", 8)]
            self.b = Booking("a", "large", self.t, self.t + timedelta(hours=1))
        def query(self, bookings=(), **kwargs):
            return available("a", kwargs.get("party", 3), kwargs.get("start", self.t),
                             kwargs.get("end", self.t + timedelta(hours=1)), self.tables,
                             bookings, kwargs.get("buffer", 15))
        def test_capacity_and_isolation(self):
            self.assertEqual(self.query(), ["large"])
            self.assertEqual(self.query([Booking("b", "large", self.t, self.b.end)]), ["large"])
        def test_overlap(self):
            self.assertEqual(self.query([self.b]), [])
        def test_turnover_boundary(self):
            self.assertEqual(self.query([self.b], start=self.b.end + timedelta(minutes=14)), [])
            self.assertEqual(self.query([self.b], start=self.b.end + timedelta(minutes=15)), ["large"])
        def test_cancelled(self):
            self.assertEqual(self.query([Booking("a", "large", self.t, self.b.end, "cancelled")]), ["large"])
        def test_invalid_time(self):
            with self.assertRaises(ValueError):
                self.query(start=datetime(2026, 11, 15, 18))
            with self.assertRaises(ValueError):
                self.query(end=self.t)
        def test_duplicate_inventory(self):
            with self.assertRaises(ValueError):
                available("a", 1, self.t, self.b.end, self.tables + [self.tables[0]], [])
        def test_invalid_booking(self):
            with self.assertRaises(ValueError):
                self.query([Booking("a", "absent", self.t, self.b.end)])
        def test_proposed_turnover(self):
            future = Booking("a", "large", self.b.end + timedelta(minutes=10), self.b.end + timedelta(hours=2))
            self.assertEqual(self.query([future]), [])
        def test_boolean_party_rejected(self):
            with self.assertRaises(ValueError):
                self.query(party=True)
    unittest.main(verbosity=2)
