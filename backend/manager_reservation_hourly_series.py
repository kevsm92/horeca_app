"""Offline manager-only hourly reservation arrivals; no inferred occupancy."""
from datetime import datetime, timedelta, timezone


def reservation_arrivals_hourly_series(*, principal, reservations, start, end):
    if not getattr(principal, 'authenticated', False) or getattr(principal, 'role', None) not in ('manager', 'owner'):
        raise PermissionError('manager authentication required')
    venue = getattr(principal, 'venue_id', None)
    if not isinstance(venue, str) or not venue.strip():
        raise PermissionError('trusted venue required')
    for instant in (start, end):
        if not isinstance(instant, datetime) or instant.tzinfo is None or instant.utcoffset() is None:
            raise ValueError('aware bounds required')
    first, last = start.astimezone(timezone.utc), end.astimezone(timezone.utc)
    if any((first.minute, first.second, first.microsecond, last.minute, last.second, last.microsecond)):
        raise ValueError('UTC hour-aligned bounds required')
    hours = int((last - first).total_seconds() // 3600)
    if not 1 <= hours <= 168 or first + timedelta(hours=hours) != last:
        raise ValueError('range must be 1..168 whole hours')
    buckets = [{'hour_start_utc': (first + timedelta(hours=i)).isoformat(),
                'scheduled_arrivals': None if reservations is None else 0} for i in range(hours)]
    if reservations is not None:
        seen = set()
        for record in reservations:
            if not isinstance(record, dict):
                raise ValueError('invalid reservation record')
            if record.get('venue_id') != venue:
                continue
            rid, status, starts = (record.get(k) for k in ('id', 'status', 'starts_at'))
            if not isinstance(rid, str) or not rid.strip() or rid in seen:
                raise ValueError('invalid or duplicate reservation ID')
            seen.add(rid)
            if status not in ('confirmed', 'seated', 'completed', 'cancelled', 'no_show'):
                raise ValueError('invalid reservation status')
            if not isinstance(starts, datetime) or starts.tzinfo is None or starts.utcoffset() is None:
                raise ValueError('aware reservation start required')
            stamp = starts.astimezone(timezone.utc)
            if status in ('confirmed', 'seated', 'completed') and first <= stamp < last:
                buckets[int((stamp - first).total_seconds() // 3600)]['scheduled_arrivals'] += 1
    return {'venue_id': venue, 'source': 'trusted_reservation_records' if reservations is not None else 'not_connected',
            'status': 'available' if reservations is not None else 'unavailable',
            'is_live': False, 'hours': buckets}
