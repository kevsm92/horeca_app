"""Offline manager snapshot; scheduled shifts do not prove attendance.

Requires a trusted server-authenticated principal and trusted storage rows.
No HTTP route, mobile punch collection or real staff data.
"""
from datetime import datetime, timedelta, timezone
from roster_presence import project_presence


def working_now(*, principal, staff, shifts, kiosk_events, as_of):
    if not getattr(principal, 'authenticated', False) or getattr(principal, 'role', None) not in ('manager', 'owner'):
        raise PermissionError('manager authentication required')
    venue = getattr(principal, 'venue_id', None)
    if not isinstance(venue, str) or not venue.strip():
        raise PermissionError('trusted venue required')
    if not isinstance(as_of, datetime) or as_of.tzinfo is None or as_of.utcoffset() is None:
        raise ValueError('aware as_of required')
    now = as_of.astimezone(timezone.utc)
    people = [p for p in staff if p['venue_id'] == venue]
    ids = [p['id'] for p in people]
    if len(ids) != len(set(ids)):
        raise ValueError('duplicate staff IDs')
    presence = {p['staff_id']: p['presence'] for p in project_presence(
        venue_id=venue, staff_ids=ids, events=kiosk_events, as_of=now)['staff']}
    current = {sid: [] for sid in ids}
    upcoming = {sid: [] for sid in ids}
    for shift in shifts:
        if shift['venue_id'] != venue or shift['staff_id'] not in current:
            continue
        start, end = shift['start_utc'], shift['end_utc']
        if any(not isinstance(t, datetime) or t.tzinfo is None or t.utcoffset() is None for t in (start, end)):
            raise ValueError('aware shift interval required')
        start, end = start.astimezone(timezone.utc), end.astimezone(timezone.utc)
        if end <= start:
            raise ValueError('invalid shift interval')
        entry = {'shift_id': shift['id'], 'station': shift['station'],
                 'start': start.isoformat(), 'end': end.isoformat()}
        if start <= now < end:
            current[shift['staff_id']].append(entry)
        elif now < start <= now + timedelta(days=7):
            upcoming[shift['staff_id']].append(entry)
    rows = [{'staff_id': p['id'], 'display_name': p['display_name'],
             'presence': presence[p['id']], 'scheduled_now': bool(current[p['id']]),
             'current_shifts': sorted(current[p['id']], key=lambda s: (s['start'], s['shift_id'])),
             'upcoming_shifts': sorted(upcoming[p['id']], key=lambda s: (s['start'], s['shift_id']))}
            for p in people]
    return {'venue_id': venue, 'as_of': now.isoformat(), 'source': 'trusted_kiosk_and_roster',
            'staff': rows, 'clocked_in_count': sum(p['presence'] == 'clocked_in' for p in rows)}
