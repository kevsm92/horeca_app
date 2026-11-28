"""Focused synthetic tests for reservation arrival series."""
import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from manager_reservation_hourly_series import reservation_arrivals_hourly_series


class ReservationSeriesTests(unittest.TestCase):
    def setUp(self):
        self.manager = SimpleNamespace(authenticated=True, role='manager', venue_id='fiction-a')
        self.start = datetime(2026, 11, 28, 8, tzinfo=timezone.utc)
        self.end = self.start + timedelta(hours=2)

    def series(self, rows):
        return reservation_arrivals_hourly_series(principal=self.manager, reservations=rows, start=self.start, end=self.end)

    def test_boundaries_status_and_tenant(self):
        def row(id, status, when, venue='fiction-a'):
            return dict(id=id, status=status, starts_at=when, venue_id=venue)
        rows = [row('a', 'confirmed', self.start), row('b', 'seated', self.start + timedelta(hours=1)),
                row('c', 'cancelled', self.start), row('d', 'confirmed', self.end),
                row('e', 'confirmed', self.start, 'fiction-b')]
        self.assertEqual([r['scheduled_arrivals'] for r in self.series(rows)['hours']], [1, 1])
        self.assertFalse(self.series(rows)['is_live'])

    def test_unavailable_distinct_from_zero(self):
        self.assertIsNone(self.series(None)['hours'][0]['scheduled_arrivals'])
        self.assertEqual(self.series([])['hours'][0]['scheduled_arrivals'], 0)

    def test_authorization(self):
        for principal in [SimpleNamespace(authenticated=False, role='manager', venue_id='fiction-a'),
                          SimpleNamespace(authenticated=True, role='staff', venue_id='fiction-a'),
                          SimpleNamespace(authenticated=True, role='manager', venue_id='')]:
            with self.assertRaises(PermissionError):
                reservation_arrivals_hourly_series(principal=principal, reservations=[], start=self.start, end=self.end)

    def test_invalid_data_and_bounds(self):
        row = dict(id='a', venue_id='fiction-a', status='confirmed', starts_at=self.start)
        for records in ([row, row], [{**row, 'starts_at': self.start.replace(tzinfo=None)}], [{**row, 'status': 'unknown'}]):
            with self.assertRaises(ValueError):
                self.series(records)
        with self.assertRaises(ValueError):
            reservation_arrivals_hourly_series(principal=self.manager, reservations=[], start=self.start, end=self.end + timedelta(hours=168))


if __name__ == '__main__':
    unittest.main()
