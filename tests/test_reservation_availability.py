"""Synthetic regression tests for the offline reservation availability reference."""
import unittest
from datetime import datetime, timedelta, timezone
from reference.reservation_availability import Table, Booking, available_tables

T = datetime(2026, 11, 15, 18, tzinfo=timezone.utc)
TABLES = [Table("a", "one", 2), Table("a", "two", 4), Table("b", "one", 8)]

class AvailabilityTests(unittest.TestCase):
    def call(self, bookings=(), **kwargs):
        args = dict(venue_id="a", party_size=3, starts_at=T,
                    ends_at=T + timedelta(hours=1), turnover_minutes=15,
                    tables=TABLES, bookings=list(bookings))
        args.update(kwargs)
        return available_tables(**args)

    def test_capacity_and_tenant_isolation(self):
        self.assertEqual(self.call([Booking("b", "two", T, T + timedelta(hours=1))]), ["two"])
    def test_overlap_blocks(self):
        self.assertEqual(self.call([Booking("a", "two", T, T + timedelta(hours=1))]), [])
    def test_turnover_blocks_adjacent(self):
        self.assertEqual(self.call([Booking("a", "two", T-timedelta(hours=1), T)]), [])
    def test_turnover_boundary_allows(self):
        self.assertEqual(self.call([Booking("a", "two", T-timedelta(hours=1,minutes=15), T-timedelta(minutes=15))]), ["two"])
    def test_cancelled_does_not_block(self):
        self.assertEqual(self.call([Booking("a", "two", T, T+timedelta(hours=1), "cancelled")]), ["two"])
    def test_invalid_interval_rejected(self):
        with self.assertRaises(ValueError): self.call(ends_at=T)
    def test_naive_time_rejected(self):
        with self.assertRaises(ValueError): self.call(starts_at=T.replace(tzinfo=None))
    def test_invalid_capacity_rejected(self):
        with self.assertRaises(ValueError): self.call(tables=[Table("a", "x", 0)])
    def test_duplicate_table_rejected(self):
        with self.assertRaises(ValueError): self.call(tables=[Table("a", "x", 4), Table("a", "x", 4)])
    def test_invalid_turnover_rejected(self):
        with self.assertRaises(ValueError): self.call(turnover_minutes=-1)

if __name__ == "__main__":
    unittest.main()
