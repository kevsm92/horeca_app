"""Offline manager-only hourly kitchen intake series from trusted fictional tickets."""
from datetime import datetime, timedelta, timezone


def kitchen_hourly_series(*, principal, tickets, as_of, hours=6):
    if not getattr(principal, 'authenticated', False) or getattr(principal, 'role', None) not in ('manager', 'owner'):
        raise PermissionError('manager authentication required')
    venue = getattr(principal, 'venue_id', None)
    if not isinstance(venue, str) or not venue.strip():
        raise PermissionError('trusted venue required')
    if not isinstance(as_of, datetime) or as_of.tzinfo is None or as_of.utcoffset() is None:
        raise ValueError('aware as_of required')
    if type(hours) is not int or not 1 <= hours <= 24:
        raise ValueError('hours must be 1..24')
    end = as_of.astimezone(timezone.utc)
    start = end.replace(minute=0, second=0, microsecond=0) - timedelta(hours=hours - 1)
    buckets = {start + timedelta(hours=i): 0 for i in range(hours)}
    if tickets is not None:
        seen = set()
        for ticket in tickets:
            if ticket['venue_id'] != venue:
                continue
            identifier = ticket.get('id')
            timestamp = ticket.get('created_at')
            if not isinstance(identifier, str) or not identifier or identifier in seen:
                raise ValueError('invalid or duplicate ticket ID')
            seen.add(identifier)
            if not isinstance(timestamp, datetime) or timestamp.tzinfo is None or timestamp.utcoffset() is None:
                raise ValueError('aware ticket timestamp required')
            timestamp = timestamp.astimezone(timezone.utc)
            if timestamp > end:
                raise ValueError('future ticket timestamp')
            bucket = timestamp.replace(minute=0, second=0, microsecond=0)
            if bucket in buckets:
                buckets[bucket] += 1
    return {'venue_id': venue, 'as_of_utc': end.isoformat(), 'is_live': False,
            'source': 'trusted_kitchen_tickets' if tickets is not None else 'not_connected',
            'series': [{'hour_utc': hour.isoformat(), 'status': 'available' if tickets is not None else 'unavailable',
                        'ticket_count': count if tickets is not None else None} for hour, count in buckets.items()]}
