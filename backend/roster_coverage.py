"""Offline, manager-authorized weekly station coverage preview (scheduled, not present)."""
from datetime import datetime, timedelta, timezone


def station_coverage(*, principal, shifts, window_start, window_end, stations):
    if not getattr(principal, 'authenticated', False) or getattr(principal, 'role', None) not in ('manager', 'owner'):
        raise PermissionError('manager authentication required')
    venue = getattr(principal, 'venue_id', None)
    if not isinstance(venue, str) or not venue.strip():
        raise PermissionError('trusted venue required')
    for t in (window_start, window_end):
        if not isinstance(t, datetime) or t.tzinfo is None or t.utcoffset() is None:
            raise ValueError('aware window required')
    begin, end = window_start.astimezone(timezone.utc), window_end.astimezone(timezone.utc)
    if not begin < end or end - begin > timedelta(days=7):
        raise ValueError('window must be positive and at most seven days')
    if len(stations) != len(set(stations)) or any(not isinstance(s, str) or not s.strip() for s in stations):
        raise ValueError('unique station names required')
    selected = []
    for shift in shifts:
        if shift['venue_id'] != venue:
            continue
        start, finish = shift['start_utc'], shift['end_utc']
        if any(not isinstance(t, datetime) or t.tzinfo is None or t.utcoffset() is None for t in (start, finish)):
            raise ValueError('aware shift required')
        start, finish = start.astimezone(timezone.utc), finish.astimezone(timezone.utc)
        if finish <= start:
            raise ValueError('invalid shift')
        if start < end and finish > begin and shift['station'] in stations:
            selected.append((shift['station'], max(start, begin), min(finish, end)))
    rows = []
    for station in stations:
        intervals = sorted((start, finish) for name, start, finish in selected if name == station)
        cursor = begin
        gaps = []
        for start, finish in intervals:
            if start > cursor:
                gaps.append({'start': cursor.isoformat(), 'end': start.isoformat()})
            cursor = max(cursor, finish)
        if cursor < end:
            gaps.append({'start': cursor.isoformat(), 'end': end.isoformat()})
        rows.append({'station': station, 'uncovered': gaps})
    return {'venue_id': venue, 'source': 'scheduled_shifts_only', 'presence': 'unknown',
            'window_start': begin.isoformat(), 'window_end': end.isoformat(), 'stations': rows}
