"""Offline weekly roster projection; not an authenticated API endpoint."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


def weekly_roster(shifts, venue_id, monday, tz_name='Europe/Brussels'):
    """Project trusted venue-scoped shifts into a Mon-Sun manager roster.

    Authentication and manager authorization must be enforced by the HTTP layer.
    Scheduled shifts do not prove actual presence.
    """
    if monday.weekday() != 0:
        raise ValueError('week_start must be Monday')
    tz = ZoneInfo(tz_name)
    begin = datetime.combine(monday, datetime.min.time(), tzinfo=tz)
    end = datetime.combine(monday + timedelta(days=7), datetime.min.time(), tzinfo=tz)
    rows = []
    seen = set()
    for s in shifts:
        if s['venue_id'] != venue_id:
            continue
        start, finish = s['start_utc'], s['end_utc']
        if start.tzinfo is None or finish.tzinfo is None or finish <= start:
            raise ValueError('invalid shift interval')
        if finish <= begin or start >= end:
            continue
        if s['id'] in seen:
            raise ValueError('duplicate shift ID')
        seen.add(s['id'])
        rows.append({'id': s['id'], 'staff_id': s['staff_id'],
                     'station': s['station'], 'start': start.astimezone(tz).isoformat(),
                     'end': finish.astimezone(tz).isoformat(),
                     'attendance': 'unknown'})
    rows.sort(key=lambda s: (s['start'], s['id']))
    return {'venue_id': venue_id, 'week_start': monday.isoformat(),
            'timezone': tz_name, 'source': 'scheduled_shifts', 'shifts': rows}


if __name__ == '__main__':
    import unittest
    from datetime import date, timezone

    class RosterTests(unittest.TestCase):
        def setUp(self):
            self.start = datetime(2026, 11, 27, 21, tzinfo=timezone.utc)
            self.shift = dict(id='s1', venue_id='v1', staff_id='fictional-1',
                              station='kitchen', start_utc=self.start,
                              end_utc=self.start + timedelta(hours=5))

        def test_cross_midnight_and_attendance_unknown(self):
            r = weekly_roster([self.shift], 'v1', date(2026, 11, 23))
            self.assertEqual(len(r['shifts']), 1)
            self.assertEqual(r['shifts'][0]['attendance'], 'unknown')
            self.assertTrue(r['shifts'][0]['end'].startswith('2026-11-28'))

        def test_tenant_isolation(self):
            self.assertEqual(weekly_roster([self.shift], 'v2', date(2026, 11, 23))['shifts'], [])

        def test_invalid_interval(self):
            with self.assertRaises(ValueError):
                weekly_roster([dict(self.shift, end_utc=self.start)], 'v1', date(2026, 11, 23))

        def test_monday_only(self):
            with self.assertRaises(ValueError):
                weekly_roster([], 'v1', date(2026, 11, 24))

    unittest.main()
