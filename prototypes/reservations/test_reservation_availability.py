import unittest
from datetime import datetime, timedelta, timezone
from reservation_availability import Table, Booking, available_tables

UTC = timezone.utc
T = datetime(2026, 11, 15, 18, tzinfo=UTC)
D = timedelta(hours=2)
TURN = timedelta(minutes=30)
TABLES = [Table('a', 'a1', 2), Table('a', 'a2', 4), Table('b', 'b1', 8)]

class AvailabilityTests(unittest.TestCase):
    def check(self, bookings=(), guests=2, start=T, turnover=TURN):
        return available_tables('a', guests, start, D, turnover, TABLES, list(bookings))

    def test_capacity_and_tenant(self):
        self.assertEqual(self.check(guests=3), ['a2'])
        self.assertEqual(self.check(guests=5), [])

    def test_overlap_and_turnover(self):
        booking = Booking('a', 'a2', T, T + D)
        self.assertEqual(self.check([booking], guests=3), [])
        self.assertEqual(self.check([booking], guests=3, start=T + D), [])
        self.assertEqual(self.check([booking], guests=3, start=T + D + TURN), ['a2'])

    def test_other_tenant_cannot_block(self):
        self.assertEqual(self.check([Booking('b', 'a2', T, T+D)], guests=3), ['a2'])

    def test_cancelled_does_not_block(self):
        self.assertEqual(self.check([Booking('a', 'a2', T, T+D, 'cancelled')], guests=3), ['a2'])

    def test_invalid_time_and_inputs(self):
        with self.assertRaises(ValueError): self.check(start=T.replace(tzinfo=None))
        with self.assertRaises(ValueError): self.check(guests=0)
        with self.assertRaises(ValueError): self.check(turnover=timedelta(minutes=-1))

    def test_boundary_just_before_booking(self):
        b = Booking('a', 'a2', T, T+D)
        self.assertEqual(self.check([b], guests=3, start=T-D-TURN), ['a2'])
        self.assertEqual(self.check([b], guests=3, start=T-D), [])

if __name__ == '__main__': unittest.main()
