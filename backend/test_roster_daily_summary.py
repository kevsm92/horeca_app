import unittest
from datetime import date, datetime, timezone
from types import SimpleNamespace
from roster_daily_summary import daily_roster_summary


class DailyRosterSummaryTests(unittest.TestCase):
    def setUp(self):
        self.manager = SimpleNamespace(authenticated=True, role='manager', venue_id='a')
        self.shifts = [dict(id='1', venue_id='a', staff_id='fictional-a', station='bar',
                            start_utc=datetime(2026, 11, 23, 8, tzinfo=timezone.utc),
                            end_utc=datetime(2026, 11, 23, 16, tzinfo=timezone.utc)),
                       dict(id='2', venue_id='b', staff_id='private-b', station='bar',
                            start_utc=datetime(2026, 11, 23, 8, tzinfo=timezone.utc),
                            end_utc=datetime(2026, 11, 23, 16, tzinfo=timezone.utc))]

    def test_daily_projection_is_scheduled_only_and_isolated(self):
        result = daily_roster_summary(principal=self.manager, shifts=self.shifts, monday=date(2026, 11, 23))
        self.assertEqual(result['days'][0]['scheduled_staff_count'], 1)
        self.assertEqual(result['days'][0]['stations'], {'bar': 1})
        self.assertEqual(result['days'][1]['scheduled_staff_count'], 0)
        self.assertEqual(result['actual_presence'], 'unknown')
        self.assertNotIn('private-b', repr(result))

    def test_staff_denied(self):
        with self.assertRaises(PermissionError):
            daily_roster_summary(principal=SimpleNamespace(authenticated=True, role='staff', venue_id='a'), shifts=self.shifts, monday=date(2026, 11, 23))

    def test_invalid_shift_rejected(self):
        with self.assertRaises(ValueError):
            daily_roster_summary(principal=self.manager, shifts=[dict(self.shifts[0], end_utc=self.shifts[0]['start_utc'])], monday=date(2026, 11, 23))

    def test_dst_week_has_seven_local_dates(self):
        result = daily_roster_summary(principal=self.manager, shifts=[], monday=date(2027, 3, 22))
        self.assertEqual(len(result['days']), 7)
        self.assertEqual(result['days'][-1]['date'], '2027-03-28')


if __name__ == '__main__':
    unittest.main()
