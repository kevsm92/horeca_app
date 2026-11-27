"""Offline draft shift-removal preview; caller must atomically CAS the revision.

Principal must originate from trusted authentication, not client headers.
"""
def prepare_shift_removal(*, principal, snapshot, expected_revision, shift_id):
    if not getattr(principal, 'authenticated', False) or getattr(principal, 'role', None) not in ('manager', 'owner'):
        raise PermissionError('manager authentication required')
    venue = getattr(principal, 'venue_id', None)
    if not isinstance(venue, str) or not venue.strip() or snapshot.get('venue_id') != venue:
        raise PermissionError('trusted venue mismatch')
    revision = snapshot.get('revision')
    if type(revision) is not int or type(expected_revision) is not int or revision < 0 or expected_revision != revision:
        raise ValueError('stale or invalid revision')
    if snapshot.get('status') != 'draft':
        raise ValueError('only draft rosters may be changed')
    if not isinstance(shift_id, str) or not shift_id.strip():
        raise ValueError('shift ID required')
    shifts = snapshot.get('shifts')
    if not isinstance(shifts, list) or any(not isinstance(s, dict) or s.get('venue_id') != venue for s in shifts):
        raise ValueError('invalid or cross-venue roster shifts')
    matches = [s for s in shifts if s.get('id') == shift_id]
    if len(matches) != 1:
        raise ValueError('shift not found or duplicate ID')
    return {'venue_id': venue, 'status': 'draft', 'shifts': [dict(s) for s in shifts if s.get('id') != shift_id],
            'expected_revision': revision, 'next_revision': revision + 1,
            'requires_atomic_compare_and_swap': True}
