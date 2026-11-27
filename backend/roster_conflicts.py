"""Offline venue-scoped roster conflict preview, not a publish authorization gate.

Input shifts must come from trusted storage. Overlapping shifts for the same
staff member are reported for manager review, never silently accepted.
"""
from datetime import timezone


def roster_conflicts(shifts, venue_id):
    """Return deterministic pairs of overlapping shift IDs within one venue."""
    scoped = []
    ids = set()
    for shift in shifts:
        if shift['venue_id'] != venue_id:
            continue
        start, end = shift['start_utc'], shift['end_utc']
        if (start.tzinfo is None or start.utcoffset() is None or
                end.tzinfo is None or end.utcoffset() is None or end <= start):
            raise ValueError('invalid shift interval')
        if shift['id'] in ids:
            raise ValueError('duplicate shift ID')
        ids.add(shift['id'])
        scoped.append((shift['staff_id'], start.astimezone(timezone.utc),
                       end.astimezone(timezone.utc), shift['id']))
    scoped.sort(key=lambda row: (row[0], row[1], row[3]))
    conflicts = []
    for i, (staff, start, end, shift_id) in enumerate(scoped):
        for other_staff, other_start, other_end, other_id in scoped[i + 1:]:
            if other_staff != staff:
                break
            if other_start >= end:
                break
            if start < other_end:
                conflicts.append({'staff_id': staff, 'shift_ids': [shift_id, other_id],
                                  'reason': 'overlap'})
    return {'venue_id': venue_id, 'conflicts': conflicts}
