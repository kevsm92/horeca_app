"""Manager-only upcoming scheduled shifts; offline projection, never attendance."""
from datetime import datetime, timedelta, timezone


def upcoming_shifts(*, principal, shifts, as_of, horizon_hours=168, limit=50):
    if not getattr(principal, 'authenticated', False) or getattr(principal, 'role', None) not in ('manager', 'owner'):
        raise PermissionError('manager authorization required')
    venue = getattr(principal, 'venue_id', None)
    if not isinstance(venue, str) or not venue.strip():
        raise PermissionError('trusted venue required')
    if not isinstance(as_of, datetime) or as_of.tzinfo is None or as_of.utcoffset() is None:
        raise ValueError('aware as_of required')
    if type(horizon_hours) is not int or not 1 <= horizon_hours <= 168:
        raise ValueError('horizon must be 1..168 hours')
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError('limit must be 1..100')
    now = as_of.astimezone(timezone.utc)
    cutoff = now + timedelta(hours=horizon_hours)
    rows, ids = [], set()
    for shift in shifts:
        if shift['venue_id'] != venue:
            continue
        start, end = shift['start_utc'], shift['end_utc']
        if any(not isinstance(t, datetime) or t.tzinfo is None or t.utcoffset() is None for t in (start, end)):
            raise ValueError('aware shift interval required')
        start, end = start.astimezone(timezone.utc), end.astimezone(timezone.utc)
        if end <= start:
            raise ValueError('invalid shift interval')
        if start < now or start >= cutoff:
            continue
        sid = shift['id']
        if sid in ids:
            raise ValueError('duplicate shift ID')
        ids.add(sid)
        rows.append({'id': sid, 'staff_id': shift['staff_id'], 'station': shift['station'],
                     'start_utc': start.isoformat(), 'end_utc': end.isoformat(),
                     'attendance': 'unknown'})
    rows.sort(key=lambda s: (s['start_utc'], s['id']))
    return {'venue_id': venue, 'source': 'scheduled_shifts_only', 'as_of': now.isoformat(),
            'horizon_hours': horizon_hours, 'total': len(rows), 'shifts': rows[:limit]}
