"""Venue-scoped informational rest-gap preview for fictional scheduled shifts.

This is not a legal compliance decision or disciplinary signal. A manager must
configure and validate the threshold against applicable Belgian rules/agreements.
"""
from datetime import timedelta, timezone


def rest_gap_review(shifts, venue_id, minimum_rest_minutes):
    if not isinstance(venue_id, str) or not venue_id.strip():
        raise ValueError('venue required')
    if type(minimum_rest_minutes) is not int or not 0 <= minimum_rest_minutes <= 10080:
        raise ValueError('invalid configured threshold')
    scoped = {}
    seen = set()
    for shift in shifts:
        if shift['venue_id'] != venue_id:
            continue
        start, end = shift['start_utc'], shift['end_utc']
        if (start.tzinfo is None or start.utcoffset() is None or
                end.tzinfo is None or end.utcoffset() is None or end <= start):
            raise ValueError('invalid shift interval')
        if shift['id'] in seen:
            raise ValueError('duplicate shift id')
        seen.add(shift['id'])
        scoped.setdefault(shift['staff_id'], []).append((start.astimezone(timezone.utc), end.astimezone(timezone.utc), shift['id']))
    flags = []
    for staff_id, rows in scoped.items():
        rows.sort()
        for previous, current in zip(rows, rows[1:]):
            gap = current[0] - previous[1]
            if gap < timedelta(minutes=minimum_rest_minutes):
                flags.append({'staff_id': staff_id, 'previous_shift_id': previous[2],
                              'next_shift_id': current[2],
                              'gap_minutes': int(gap.total_seconds() // 60),
                              'reason': 'overlap' if gap.total_seconds() < 0 else 'below_configured_rest_gap',
                              'review_required': True})
    flags.sort(key=lambda item: (item['staff_id'], item['previous_shift_id'], item['next_shift_id']))
    return {'venue_id': venue_id, 'source': 'scheduled_not_attendance',
            'threshold_minutes': minimum_rest_minutes, 'review_flags': flags,
            'legal_compliance_determined': False}
