"""Offline manager kitchen-ticket KPI; caller supplies trusted records, not HTTP."""
from datetime import datetime, timezone


def kitchen_kpis(*, principal, tickets, as_of):
    if not getattr(principal, 'authenticated', False) or getattr(principal, 'role', None) not in ('manager', 'owner'):
        raise PermissionError('manager authentication required')
    venue = getattr(principal, 'venue_id', None)
    if not isinstance(venue, str) or not venue.strip():
        raise PermissionError('trusted venue required')
    if not isinstance(as_of, datetime) or as_of.tzinfo is None or as_of.utcoffset() is None:
        raise ValueError('aware as_of required')
    now = as_of.astimezone(timezone.utc)
    if tickets is None:
        metric = {'status': 'unavailable', 'value': None}
        source = 'not_connected'
    else:
        seen = set()
        count = 0
        for ticket in tickets:
            if ticket['venue_id'] != venue:
                continue
            ticket_id = ticket.get('id')
            state = ticket.get('status')
            created = ticket.get('created_at')
            if not isinstance(ticket_id, str) or not ticket_id or ticket_id in seen:
                raise ValueError('invalid or duplicate ticket ID')
            seen.add(ticket_id)
            if state not in ('queued', 'preparing', 'ready', 'handed_off', 'voided'):
                raise ValueError('unknown ticket status')
            if not isinstance(created, datetime) or created.tzinfo is None or created.utcoffset() is None:
                raise ValueError('aware ticket creation required')
            if created.astimezone(timezone.utc) > now:
                raise ValueError('future ticket creation')
            if state in ('queued', 'preparing', 'ready'):
                count += 1
        metric = {'status': 'available', 'value': count}
        source = 'trusted_ticket_records'
    return {'venue_id': venue, 'as_of_utc': now.isoformat(), 'source': source,
            'open_kitchen_tickets': metric, 'is_live': False}
