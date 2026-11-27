import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from roster_publication_readiness import publication_readiness

T = datetime(2026, 11, 23, tzinfo=timezone.utc)
M = SimpleNamespace(authenticated=True, role='manager', venue_id='v1')


def shift(id, staff, station, hour, venue='v1'):
    return dict(id=id, staff_id=staff, station=station, venue_id=venue,
                start_utc=T + timedelta(hours=hour), end_utc=T + timedelta(hours=hour + 4))


class ReadinessTests(unittest.TestCase):
    def run_check(self, principal=M, shifts=(), stations=('bar',)):
        return publication_readiness(principal=principal, shifts=shifts, week_start=T,
                                     week_end=T + timedelta(days=7), required_stations=stations)

    def test_no_schedule_is_not_ready(self):
        result = self.run_check()
        self.assertEqual(result['stations_without_shifts'], ['bar'])
        self.assertFalse(result['ready_for_manager_review'])
        self.assertFalse(result['published'])

    def test_cross_venue_excluded_and_scheduled_not_present(self):
        result = self.run_check(shifts=[shift('x', 'a', 'bar', 1, 'v2'), shift('y', 'b', 'bar', 2)])
        self.assertEqual(result['shift_count'], 1)
        self.assertEqual(result['actual_presence'], 'unknown')
        self.assertTrue(result['ready_for_manager_review'])

    def test_overlap_blocks_review(self):
        result = self.run_check(shifts=[shift('a', 's', 'bar', 0), shift('b', 's', 'bar', 2)])
        self.assertEqual(result['overlap_pairs'], [('a', 'b')])
        self.assertFalse(result['ready_for_manager_review'])

    def test_manager_only(self):
        for principal in (SimpleNamespace(authenticated=False, role='manager', venue_id='v1'),
                          SimpleNamespace(authenticated=True, role='staff', venue_id='v1')):
            with self.assertRaises(PermissionError):
                self.run_check(principal=principal)

    def test_rejects_invalid_shift_and_duplicate_ids(self):
        with self.assertRaises(ValueError):
            self.run_check(shifts=[shift('a', 's', 'bar', 0), shift('a', 't', 'bar', 1)])
        bad = shift('z', 's', 'bar', 0)
        bad['end_utc'] = bad['start_utc']
        with self.assertRaises(ValueError):
            self.run_check(shifts=[bad])


if __name__ == '__main__':
    unittest.main()
