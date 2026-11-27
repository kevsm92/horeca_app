import unittest
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace
from manager_roster_access import manager_weekly_roster


class ManagerRosterAccessTests(unittest.TestCase):
    def setUp(self):
        self.manager = SimpleNamespace(authenticated=True, role='manager', venue_id='v1')
        start = datetime(2026, 11, 27, 21, tzinfo=timezone.utc)
        self.shifts = [
            dict(id='a', venue_id='v1', staff_id='fictional-1', station='bar',
                 start_utc=start, end_utc=start + timedelta(hours=5)),
            dict(id='b', venue_id='v2', staff_id='fictional-2', station='kitchen',
                 start_utc=start, end_utc=start + timedelta(hours=2)),
        ]

    def project(self, **kwargs):
        args = dict(principal=self.manager, shifts=self.shifts, monday=date(2026, 11, 23))
        args.update(kwargs)
        return manager_weekly_roster(**args)

    def test_scoped_cross_midnight_and_unknown_attendance(self):
        result = self.project()
        self.assertEqual([s['id'] for s in result['shifts']], ['a'])
        self.assertEqual(result['shifts'][0]['attendance'], 'unknown')
        self.assertTrue(result['shifts'][0]['end'].startswith('2026-11-28'))

    def test_denied_unauthenticated_and_staff(self):
        for principal in [
            SimpleNamespace(authenticated=False, role='manager', venue_id='v1'),
            SimpleNamespace(authenticated=True, role='staff', venue_id='v1'),
            SimpleNamespace(authenticated=True, role='owner', venue_id=''),
        ]:
            with self.assertRaises(PermissionError):
                self.project(principal=principal)

    def test_server_venue_scoping(self):
        other = SimpleNamespace(authenticated=True, role='owner', venue_id='v2')
        self.assertEqual([s['id'] for s in self.project(principal=other)['shifts']], ['b'])

    def test_invalid_week_rejected(self):
        with self.assertRaises(ValueError):
            self.project(monday=date(2026, 11, 24))
        with self.assertRaises(ValueError):
            self.project(monday='2026-11-23')


if __name__ == '__main__':
    unittest.main()
