"""Offline, synthetic-data weekly roster read model; not an HTTP endpoint."""
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

BRUSSELS = ZoneInfo('Europe/Brussels')

class RosterAccessError(PermissionError):
    pass


def weekly_roster(*, actor, venue_id, monday, shifts):
    """Return a venue-isolated Mon-Sun snapshot with scheduled-only semantics.

    actor is a trusted authenticated server-side principal, never request JSON.
    Shift timestamps must be timezone-aware ISO strings and may cross midnight.
    """
    if not actor or actor.get('role') not in ('manager', 'owner') or actor.get('venue_id') != venue_id:
        raise RosterAccessError('manager access required for venue')
    if not isinstance(monday, date) or isinstance(monday, datetime) or monday.weekday() != 0:
        raise ValueError('week must begin Monday')
    end = monday + timedelta(days=7)
    entries = []
    for shift in shifts:
        if shift['venue_id'] != venue_id:
            continue
        start = datetime.fromisoformat(shift['starts_at'])
        finish = datetime.fromisoformat(shift['ends_at'])
        if start.tzinfo is None or finish.tzinfo is None or finish <= start:
            raise ValueError('invalid timezone-aware shift interval')
        local_start = start.astimezone(BRUSSELS)
        local_end = finish.astimezone(BRUSSELS)
        if local_start.date() < end and local_end.date() >= monday and local_end > datetime.combine(monday, datetime.min.time(), BRUSSELS):
            entries.append({'shift_id': shift['id'], 'staff_id': shift['staff_id'],
                            'station': shift['station'], 'starts_at': local_start.isoformat(),
                            'ends_at': local_end.isoformat(), 'status': 'scheduled',
                            'attendance': 'unknown'})
    entries.sort(key=lambda x: (x['starts_at'], x['shift_id']))
    return {'venue_id': venue_id, 'week_start': monday.isoformat(),
            'week_end_exclusive': end.isoformat(), 'source': 'scheduled_shifts',
            'attendance_is_inferred': False, 'shifts': entries}
