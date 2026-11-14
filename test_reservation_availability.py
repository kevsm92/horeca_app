import unittest
from datetime import datetime, timedelta, timezone
from reservation_availability import Table, Occupancy, available_tables

T = datetime(2026, 11, 15, 18, tzinfo=timezone.utc)
H = timedelta(hours=1)
M = timedelta(minutes=15)
TABLES = (Table('a', 't1', 2), Table('a', 't2', 4), Table('b', 't3', 10))

def check(size=2, at=T, bookings=(), turnover=M, tables=TABLES):
    return available_tables('a', size, at, H, turnover, tables, bookings)

class ReservationAvailabilityTests(unittest.TestCase):
    def test_capacity_and_tenant(self):
        self.assertEqual(check(size=3), ('t2',))
    def test_overlapping_and_turnover(self):
        b = Occupancy('a', 't1', T-H, T, 'confirmed')
        self.assertEqual(check(bookings=(b,)), ('t2',))
        self.assertEqual(check(at=T+M, bookings=(b,)), ('t1', 't2'))
    def test_cancelled_does_not_block(self):
        b = Occupancy('a', 't1', T, T+H, 'cancelled')
        self.assertEqual(check(bookings=(b,)), ('t1', 't2'))
    def test_other_venue_does_not_block(self):
        b = Occupancy('b', 't3', T, T+H, 'seated')
        self.assertEqual(check(bookings=(b,)), ('t1', 't2'))
    def test_invalid_input_fails_closed(self):
        with self.assertRaises(ValueError): check(size=True)
        with self.assertRaises(ValueError): check(at=T.replace(tzinfo=None))
        with self.assertRaises(ValueError): check(tables=(TABLES[0], TABLES[0]))
        with self.assertRaises(ValueError): check(bookings=(Occupancy('a', 'missing', T, T+H, 'confirmed'),))
    def test_half_open_boundary_without_turnover(self):
        b = Occupancy('a', 't1', T-H, T, 'confirmed')
        self.assertEqual(check(bookings=(b,), turnover=timedelta(0)), ('t1', 't2'))

if __name__ == '__main__':
    unittest.main()
