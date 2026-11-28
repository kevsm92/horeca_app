"""Manager-only daily scheduled staffing summary, never an attendance claim."""
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo


def daily_roster_summary(*, principal, shifts, monday, tz_name='Europe/Brussels'):
    if not getattr(principal, 'authenticated', False) or getattr(principal, 'role', None) not in ('manager', 'owner'):
        raise PermissionError('manager authorization required')
    venue = getattr(principal, 'venue_id', None)
    if not isinstance(venue, str) or not venue.strip():
        raise PermissionError('trusted venue required')
    if not isinstance(monday, date) or isinstance(monday, datetime) or monday.weekday() != 0:
        raise ValueError('Monday date required')
    tz = ZoneInfo(tz_name)
    days = []
    for offset in range(7):
        day = monday + timedelta(days=offset)
        begin = datetime.combine(day, datetime.min.time(), tzinfo=tz).astimezone(timezone.utc)
        end = datetime.combine(day + timedelta(days=1), datetime.min.time(), tzinfo=tz).astimezone(timezone.utc)
        staff, stations = set(), {}
        ids = set()
        for shift in shifts:
            if shift['venue_id'] != venue:
                continue
            start, finish = shift['start_utc'], shift['end_utc']
            if any(not isinstance(t, datetime) or t.tzinfo is None or t.utcoffset() is None for t in (start, finish)):
                raise ValueError('aware shift timestamps required')
            start, finish = start.astimezone(timezone.utc), finish.astimezone(timezone.utc)
            if finish <= start:
                raise ValueError('invalid shift interval')
            if not (start < end and finish > begin):
                continue
            if shift['id'] in ids:
                raise ValueError('duplicate shift ID')
            ids.add(shift['id'])
            staff.add(shift['staff_id'])
            stations.setdefault(shift['station'], set()).add(shift['staff_id'])
        days.append({'date': day.isoformat(), 'scheduled_staff_count': len(staff),
                     'stations': {name: len(stations[name]) for name in sorted(stations)}})
    return {'venue_id': venue, 'week_start': monday.isoformat(), 'timezone': tz_name,
            'source': 'scheduled_shifts_only', 'actual_presence': 'unknown', 'days': days}
