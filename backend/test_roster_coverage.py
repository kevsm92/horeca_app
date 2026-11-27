import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from roster_coverage import station_coverage


class CoverageTests(unittest.TestCase):
    def setUp(self):
        self.start = datetime(2026, 11, 30, 8, tzinfo=timezone.utc)
        self.manager = SimpleNamespace(authenticated=True, role='manager', venue_id='a')
        self.shift = {'venue_id': 'a', 'station': 'bar', 'start_utc': self.start + timedelta(hours=1),
                      'end_utc': self.start + timedelta(hours=3)}

    def run_coverage(self, **kwargs):
        params = dict(principal=self.manager, shifts=[self.shift], window_start=self.start,
                      window_end=self.start + timedelta(hours=4), stations=['bar', 'kitchen'])
        params.update(kwargs)
        return station_coverage(**params)

    def test_gaps_and_no_presence_claim(self):
        result = self.run_coverage()
        self.assertEqual(result['presence'], 'unknown')
        self.assertEqual(len(result['stations'][0]['uncovered']), 2)
        self.assertEqual(len(result['stations'][1]['uncovered']), 1)

    def test_overlapping_shifts_merge(self):
        extra = dict(self.shift, start_utc=self.start + timedelta(hours=2),
                     end_utc=self.start + timedelta(hours=4))
        self.assertEqual(len(self.run_coverage(shifts=[self.shift, extra])['stations'][0]['uncovered']), 1)

    def test_cross_venue_is_ignored(self):
        other = dict(self.shift, venue_id='b')
        self.assertEqual(len(self.run_coverage(shifts=[other])['stations'][0]['uncovered']), 1)

    def test_staff_denied(self):
        with self.assertRaises(PermissionError):
            self.run_coverage(principal=SimpleNamespace(authenticated=True, role='staff', venue_id='a'))

    def test_bad_window_denied(self):
        with self.assertRaises(ValueError):
            self.run_coverage(window_end=self.start + timedelta(days=8))

    def test_invalid_shift_denied(self):
        with self.assertRaises(ValueError):
            self.run_coverage(shifts=[dict(self.shift, end_utc=self.start)])


if __name__ == '__main__':
    unittest.main()
