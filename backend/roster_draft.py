"""Offline manager shift-draft validation; persistence must atomically CAS revision."""
from datetime import datetime, timezone


def prepare_shift_draft(*, principal, snapshot, expected_revision, shift, staff, stations):
    if not getattr(principal, 'authenticated', False) or getattr(principal, 'role', None) not in ('manager', 'owner'):
        raise PermissionError('manager authentication required')
    venue = getattr(principal, 'venue_id', None)
    if not isinstance(venue, str) or not venue.strip() or snapshot.get('venue_id') != venue:
        raise PermissionError('venue mismatch')
    revision = snapshot.get('revision')
    if type(expected_revision) is not int or type(revision) is not int or revision < 0 or expected_revision != revision:
        raise ValueError('invalid or stale revision')
    if snapshot.get('status') == 'published':
        raise ValueError('published roster requires separate amendment workflow')
    if shift.get('venue_id') != venue or shift.get('staff_id') not in {p['id'] for p in staff if p['venue_id'] == venue}:
        raise ValueError('staff must belong to venue')
    if shift.get('station') not in {s['id'] for s in stations if s['venue_id'] == venue}:
        raise ValueError('station must belong to venue')
    start, end = shift.get('start_utc'), shift.get('end_utc')
    if any(not isinstance(t, datetime) or t.tzinfo is None or t.utcoffset() is None for t in (start, end)):
        raise ValueError('aware shift times required')
    if end <= start:
        raise ValueError('shift must end after start')
    if not isinstance(shift.get('id'), str) or not shift['id'].strip():
        raise ValueError('shift ID required')
    return {'venue_id': venue, 'expected_revision': revision, 'next_revision': revision + 1,
            'status': 'draft', 'requires_atomic_compare_and_swap': True,
            'shift': {'id': shift['id'], 'staff_id': shift['staff_id'], 'station': shift['station'],
                      'start_utc': start.astimezone(timezone.utc).isoformat(),
                      'end_utc': end.astimezone(timezone.utc).isoformat()}}
