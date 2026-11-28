"""Offline optimistic roster publication gate; no notifications or HTTP exposure.

The caller must supply a server-authenticated principal and trusted persisted
roster snapshot. Storage must atomically compare-and-swap the revision on write.
"""
from datetime import timezone


def prepare_roster_publish(*, principal, snapshot, expected_revision, shifts, published_at):
    if not getattr(principal, 'authenticated', False) or getattr(principal, 'role', None) not in ('manager', 'owner'):
        raise PermissionError('manager authentication required')
    venue = getattr(principal, 'venue_id', None)
    if not isinstance(venue, str) or not venue.strip() or snapshot.get('venue_id') != venue:
        raise PermissionError('venue scope mismatch')
    if type(expected_revision) is not int or expected_revision < 0:
        raise ValueError('invalid expected revision')
    revision = snapshot.get('revision')
    if type(revision) is not int or revision < 0:
        raise ValueError('invalid stored revision')
    if revision != expected_revision:
        raise ValueError('stale roster revision')
    if published_at.tzinfo is None or published_at.utcoffset() is None:
        raise ValueError('published_at must be timezone-aware')
    from roster_conflicts import roster_conflicts
    conflicts = roster_conflicts(shifts, venue)['conflicts']
    if conflicts:
        raise ValueError('overlapping shifts cannot be published')
    # Never mutate the trusted input; this is a proposed write, not a committed one.
    return {'venue_id': venue, 'expected_revision': revision,
            'next_revision': revision + 1, 'status': 'published',
            'published_at': published_at.astimezone(timezone.utc).isoformat(),
            'shift_ids': [s['id'] for s in shifts if s['venue_id'] == venue],
            'requires_atomic_compare_and_swap': True}
