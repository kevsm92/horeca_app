"""Manager-only offline order KPIs; accepted order value is not captured revenue.

Caller supplies server-authenticated principal and trusted order records. This is
not an HTTP endpoint and does not activate transactions.
"""
from datetime import datetime, timezone


def order_kpis(*, principal, orders, as_of):
    if not getattr(principal, 'authenticated', False) or getattr(principal, 'role', None) not in ('manager', 'owner'):
        raise PermissionError('manager authentication required')
    venue = getattr(principal, 'venue_id', None)
    if not isinstance(venue, str) or not venue.strip():
        raise PermissionError('trusted venue required')
    if not isinstance(as_of, datetime) or as_of.tzinfo is None or as_of.utcoffset() is None:
        raise ValueError('aware as_of required')
    now = as_of.astimezone(timezone.utc)
    if orders is None:
        accepted = {'status': 'unavailable', 'value': None}
        value = {'status': 'unavailable', 'value_cents': None, 'currency': 'EUR'}
    else:
        ids = set()
        count = total = 0
        for order in orders:
            if order['venue_id'] != venue:
                continue
            oid, status, cents, timestamp = (order.get(k) for k in ('id', 'status', 'total_cents', 'accepted_at'))
            if not isinstance(oid, str) or not oid or oid in ids:
                raise ValueError('invalid or duplicate order ID')
            ids.add(oid)
            if status not in ('draft', 'accepted', 'cancelled'):
                raise ValueError('unknown order status')
            if type(cents) is not int or cents < 0:
                raise ValueError('invalid integer-cent order total')
            if status == 'accepted':
                if not isinstance(timestamp, datetime) or timestamp.tzinfo is None or timestamp.utcoffset() is None:
                    raise ValueError('accepted order requires aware timestamp')
                if timestamp.astimezone(timezone.utc) > now:
                    raise ValueError('future acceptance timestamp')
                count += 1
                total += cents
        accepted = {'status': 'available', 'value': count}
        value = {'status': 'available', 'value_cents': total, 'currency': 'EUR'}
    return {'venue_id': venue, 'as_of_utc': now.isoformat(), 'source': 'trusted_order_records' if orders is not None else 'not_connected',
            'accepted_orders': accepted, 'accepted_order_value': value,
            'captured_revenue': {'status': 'unavailable', 'value_cents': None, 'currency': 'EUR'},
            'is_live': False}
