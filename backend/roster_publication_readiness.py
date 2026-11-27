"""Offline manager-only roster publication readiness; advisory, never publishes."""
from datetime import datetime, timezone


def publication_readiness(*, principal, shifts, week_start, week_end, required_stations):
    if not getattr(principal, 'authenticated', False) or getattr(principal, 'role', None) not in ('manager', 'owner'):
        raise PermissionError('manager authentication required')
    venue = getattr(principal, 'venue_id', None)
    if not isinstance(venue, str) or not venue.strip():
        raise PermissionError('trusted venue required')
    for t in (week_start, week_end):
        if not isinstance(t, datetime) or t.tzinfo is None or t.utcoffset() is None:
            raise ValueError('aware boundaries required')
    start, end = week_start.astimezone(timezone.utc), week_end.astimezone(timezone.utc)
    if not start < end or (end - start).total_seconds() != 7 * 86400:
        raise ValueError('exactly seven days required')
    if len(set(required_stations)) != len(required_stations) or any(not isinstance(s, str) or not s.strip() for s in required_stations):
        raise ValueError('unique nonempty stations required')
    selected = []
    for s in shifts:
        if s['venue_id'] != venue:
            continue
        a, b = s['start_utc'], s['end_utc']
        if any(not isinstance(t, datetime) or t.tzinfo is None or t.utcoffset() is None for t in (a, b)):
            raise ValueError('aware shifts required')
        a, b = a.astimezone(timezone.utc), b.astimezone(timezone.utc)
        if a >= b:
            raise ValueError('invalid shift interval')
        if a < end and b > start:
            selected.append((s['id'], s['staff_id'], s['station'], a, b))
    if len({s[0] for s in selected}) != len(selected):
        raise ValueError('duplicate shift IDs')
    conflicts = []
    for i, left in enumerate(selected):
        for right in selected[i + 1:]:
            if left[1] == right[1] and left[3] < right[4] and right[3] < left[4]:
                conflicts.append(tuple(sorted((left[0], right[0]))))
    missing = sorted(set(required_stations) - {s[2] for s in selected})
    blockers = []
    if conflicts:
        blockers.append('overlapping_staff_shifts')
    if missing:
        blockers.append('stations_without_any_scheduled_shift')
    return {'venue_id': venue, 'source': 'scheduled_shifts_only', 'actual_presence': 'unknown',
            'week_start': start.isoformat(), 'week_end': end.isoformat(),
            'shift_count': len(selected), 'overlap_pairs': sorted(conflicts),
            'stations_without_shifts': missing, 'advisory_blockers': blockers,
            'ready_for_manager_review': not blockers, 'published': False}
