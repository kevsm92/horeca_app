"""Manager-only scheduled station-hours projection; not actual labour or presence."""
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo


def scheduled_station_hours(*, principal, shifts, monday, tz_name='Europe/Brussels'):
    if not getattr(principal, 'authenticated', False) or getattr(principal, 'role', None) not in ('manager', 'owner'):
        raise PermissionError('manager authorization required')
    venue = getattr(principal, 'venue_id', None)
    if not isinstance(venue, str) or not venue.strip():
        raise PermissionError('trusted venue required')
    if not isinstance(monday, date) or isinstance(monday, datetime) or monday.weekday() != 0:
        raise ValueError('Monday date required')
    tz = ZoneInfo(tz_name)
    begin = datetime.combine(monday, datetime.min.time(), tzinfo=tz).astimezone(timezone.utc)
    end = datetime.combine(monday + timedelta(days=7), datetime.min.time(), tzinfo=tz).astimezone(timezone.utc)
    minutes = {}
    seen = set()
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
        if shift['id'] in seen:
            raise ValueError('duplicate shift ID')
        seen.add(shift['id'])
        station = shift['station']
        if not isinstance(station, str) or not station.strip():
            raise ValueError('station required')
        duration = (min(finish, end) - max(start, begin)).total_seconds() / 60
        minutes[station] = minutes.get(station, 0) + duration
    return {'venue_id': venue, 'week_start': monday.isoformat(), 'timezone': tz_name,
            'source': 'scheduled_shifts_only', 'actual_presence': 'unknown',
            'station_minutes': {key: minutes[key] for key in sorted(minutes)}}
