import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from manager_working_now import working_now


class WorkingNowTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 27, 8, tzinfo=timezone.utc)
        self.manager = SimpleNamespace(authenticated=True, role='manager', venue_id='v1')
        self.staff = [dict(id='s1', venue_id='v1', display_name='Fictional Alex'),
                      dict(id='s2', venue_id='v1', display_name='Fictional Sam'),
                      dict(id='other', venue_id='v2', display_name='Private')]
        self.shifts = [dict(id='shift1', venue_id='v1', staff_id='s1', station='bar',
                            start_utc=self.now - timedelta(hours=1), end_utc=self.now + timedelta(hours=2)),
                       dict(id='shift2', venue_id='v1', staff_id='s2', station='kitchen',
                            start_utc=self.now + timedelta(days=1), end_utc=self.now + timedelta(days=1, hours=3))]
        self.events = [dict(event_id='e1', venue_id='v1', staff_id='s2', source='kiosk',
                            kind='in', occurred_at=self.now - timedelta(minutes=5))]

    def run_snapshot(self, **overrides):
        args = dict(principal=self.manager, staff=self.staff, shifts=self.shifts,
                    kiosk_events=self.events, as_of=self.now)
        args.update(overrides)
        return working_now(**args)

    def test_scheduled_not_presence_and_upcoming(self):
        result = self.run_snapshot()
        self.assertEqual(result['clocked_in_count'], 1)
        self.assertEqual(result['staff'][0]['presence'], 'unknown')
        self.assertTrue(result['staff'][0]['scheduled_now'])
        self.assertEqual(result['staff'][1]['presence'], 'clocked_in')
        self.assertFalse(result['staff'][1]['scheduled_now'])
        self.assertEqual(result['staff'][1]['upcoming_shifts'][0]['station'], 'kitchen')

    def test_tenant_isolation(self):
        result = self.run_snapshot(shifts=self.shifts + [dict(self.shifts[0], venue_id='v2')])
        self.assertEqual(len(result['staff']), 2)
        self.assertNotIn('Private', str(result))

    def test_manager_gate(self):
        for role in ('staff', 'guest'):
            with self.assertRaises(PermissionError):
                self.run_snapshot(principal=SimpleNamespace(authenticated=True, role=role, venue_id='v1'))
        with self.assertRaises(PermissionError):
            self.run_snapshot(principal=SimpleNamespace(authenticated=False, role='manager', venue_id='v1'))

    def test_invalid_shift_and_non_kiosk_rejected(self):
        with self.assertRaises(ValueError):
            self.run_snapshot(shifts=[dict(self.shifts[0], end_utc=self.now - timedelta(hours=2))])
        with self.assertRaises(ValueError):
            self.run_snapshot(kiosk_events=[dict(self.events[0], source='mobile')])


if __name__ == '__main__':
    unittest.main()
