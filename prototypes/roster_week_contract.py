"""Offline, synthetic-only weekly roster contract prototype (not an HTTP endpoint).

A manager's venue comes from trusted authentication context, never a request parameter.
No database, publishing, notifications, or attendance inference is implemented here.
"""
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
import unittest

BRUSSELS = ZoneInfo('Europe/Brussels')


@dataclass(frozen=True)
class ManagerContext:
    venue_id: str
    role: str


@dataclass(frozen=True)
class Shift:
    venue_id: str
    staff_id: str
    station: str
    starts_at: datetime
    ends_at: datetime


def weekly_roster(context: ManagerContext, week_start: date, shifts: tuple[Shift, ...]):
    """Return authorized planned shifts for Monday-Sunday in Brussels local time.

    A shift crossing a week boundary appears in each week it overlaps. Presence
    is deliberately absent; a scheduled shift is never evidence of clock-in.
    """
    if context.role not in {'manager', 'owner'} or not context.venue_id:
        raise PermissionError('manager authorization required')
    if week_start.weekday() != 0:
        raise ValueError('week_start must be Monday')
    start = datetime.combine(week_start, datetime.min.time(), BRUSSELS)
    end = datetime.combine(week_start + timedelta(days=7), datetime.min.time(), BRUSSELS)
    rows = []
    for shift in shifts:
        if shift.venue_id != context.venue_id:
            continue
        if shift.starts_at.tzinfo is None or shift.ends_at.tzinfo is None:
            raise ValueError('shift timestamps must be timezone aware')
        if shift.starts_at >= shift.ends_at:
            raise ValueError('shift end must follow start')
        if shift.starts_at < end and shift.ends_at > start:
            rows.append({'staff_id': shift.staff_id, 'station': shift.station,
                         'starts_at': shift.starts_at.isoformat(),
                         'ends_at': shift.ends_at.isoformat(), 'status': 'scheduled'})
    rows.sort(key=lambda row: (row['starts_at'], row['staff_id']))
    return {'week_start': week_start.isoformat(), 'timezone': 'Europe/Brussels',
            'source': 'synthetic_planned_shifts', 'shifts': rows,
            'actual_presence': None}


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.ctx = ManagerContext('venue-a', 'manager')
        self.monday = date(2026, 11, 23)
        self.shift = Shift('venue-a', 'worker-1', 'kitchen',
                           datetime(2026, 11, 29, 23, tzinfo=BRUSSELS),
                           datetime(2026, 11, 30, 2, tzinfo=BRUSSELS))

    def test_cross_midnight_boundary(self):
        self.assertEqual(len(weekly_roster(self.ctx, self.monday, (self.shift,))['shifts']), 1)
        self.assertEqual(len(weekly_roster(self.ctx, date(2026, 11, 30), (self.shift,))['shifts']), 1)

    def test_tenant_isolation(self):
        other = Shift('venue-b', 'private-worker', 'bar', self.shift.starts_at, self.shift.ends_at)
        result = weekly_roster(self.ctx, self.monday, (self.shift, other))
        self.assertEqual([x['staff_id'] for x in result['shifts']], ['worker-1'])
        self.assertIsNone(result['actual_presence'])

    def test_authorization(self):
        with self.assertRaises(PermissionError):
            weekly_roster(ManagerContext('venue-a', 'staff'), self.monday, (self.shift,))

    def test_monday_required(self):
        with self.assertRaises(ValueError):
            weekly_roster(self.ctx, date(2026, 11, 24), (self.shift,))

    def test_naive_timestamp_rejected(self):
        invalid = Shift('venue-a', 'worker-1', 'bar', datetime(2026, 11, 24), self.shift.ends_at)
        with self.assertRaises(ValueError):
            weekly_roster(self.ctx, self.monday, (invalid,))

    def test_invalid_interval_rejected(self):
        invalid = Shift('venue-a', 'worker-1', 'bar', self.shift.ends_at, self.shift.starts_at)
        with self.assertRaises(ValueError):
            weekly_roster(self.ctx, self.monday, (invalid,))


if __name__ == '__main__':
    unittest.main()
