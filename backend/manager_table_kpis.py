"""Offline manager table occupancy KPI from trusted physical-table snapshots.

Not an HTTP endpoint. A reservation or an order alone never proves occupancy.
"""
from datetime import datetime, timezone


def table_kpis(*, principal, tables, as_of):
    if not getattr(principal, 'authenticated', False) or getattr(principal, 'role', None) not in ('manager', 'owner'):
        raise PermissionError('manager authentication required')
    venue = getattr(principal, 'venue_id', None)
    if not isinstance(venue, str) or not venue.strip():
        raise PermissionError('trusted venue required')
    if not isinstance(as_of, datetime) or as_of.tzinfo is None or as_of.utcoffset() is None:
        raise ValueError('aware as_of required')
    now = as_of.astimezone(timezone.utc)
    counts = None
    if tables is not None:
        ids = set()
        counts = {'physical_tables': 0, 'occupied_tables': 0, 'seated_guests': 0, 'physical_seats': 0}
        for table in tables:
            if not isinstance(table, dict):
                raise ValueError('invalid table record')
            if table.get('venue_id') != venue:
                continue
            tid = table.get('id')
            capacity = table.get('capacity')
            guests = table.get('seated_guests')
            if not isinstance(tid, str) or not tid.strip() or tid in ids:
                raise ValueError('invalid or duplicate physical table ID')
            ids.add(tid)
            if type(capacity) is not int or not 1 <= capacity <= 100 or type(guests) is not int or not 0 <= guests <= capacity:
                raise ValueError('invalid capacity or seated guests')
            occupied = table.get('occupied')
            if type(occupied) is not bool or occupied != (guests > 0):
                raise ValueError('occupancy and seated guest count disagree')
            observed = table.get('observed_at')
            if not isinstance(observed, datetime) or observed.tzinfo is None or observed.utcoffset() is None or observed.astimezone(timezone.utc) > now:
                raise ValueError('trusted aware observation timestamp required')
            counts['physical_tables'] += 1
            counts['occupied_tables'] += int(occupied)
            counts['seated_guests'] += guests
            counts['physical_seats'] += capacity
    return {'venue_id': venue, 'as_of_utc': now.isoformat(), 'source': 'trusted_table_snapshots' if counts is not None else 'not_connected',
            'metrics': {key: {'status': 'unavailable' if counts is None else 'available', 'value': None if counts is None else counts[key]}
                        for key in ('physical_tables', 'occupied_tables', 'seated_guests', 'physical_seats')},
            'is_live': False}
