import unittest
from datetime import date, datetime, timezone
from types import SimpleNamespace
from roster_station_hours import scheduled_station_hours

class Tests(unittest.TestCase):
    def setUp(self):
        self.manager = SimpleNamespace(authenticated=True, role='manager', venue_id='a')
        self.shift = dict(id='s', venue_id='a', station='bar', start_utc=datetime(2026, 11, 22, 23, tzinfo=timezone.utc), end_utc=datetime(2026, 11, 23, 2, tzinfo=timezone.utc))
    def test_week_boundary_and_isolation(self):
        result = scheduled_station_hours(principal=self.manager, shifts=[self.shift, dict(self.shift, id='other', venue_id='b')], monday=date(2026, 11, 23))
        self.assertEqual(result['station_minutes'], {'bar': 180})
        self.assertEqual(result['actual_presence'], 'unknown')
    def test_denied(self):
        with self.assertRaises(PermissionError):
            scheduled_station_hours(principal=SimpleNamespace(authenticated=True, role='staff', venue_id='a'), shifts=[], monday=date(2026, 11, 23))
    def test_duplicate(self):
        with self.assertRaises(ValueError):
            scheduled_station_hours(principal=self.manager, shifts=[self.shift, self.shift], monday=date(2026, 11, 23))
    def test_naive(self):
        with self.assertRaises(ValueError):
            scheduled_station_hours(principal=self.manager, shifts=[dict(self.shift, start_utc=datetime(2026, 11, 23))], monday=date(2026, 11, 23))

if __name__ == '__main__': unittest.main()
