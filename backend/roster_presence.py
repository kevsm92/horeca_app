"""Offline venue-scoped attendance projection from trusted kiosk punch events.

No HTTP route, mobile punch intake, employee scoring, or inferred presence.
"""
from datetime import datetime, timezone


def project_presence(*, venue_id, staff_ids, events, as_of):
    """Project trusted kiosk events; scheduled shifts never imply presence."""
    if not isinstance(venue_id, str) or not venue_id.strip():
        raise ValueError('venue required')
    if not isinstance(as_of, datetime) or as_of.tzinfo is None or as_of.utcoffset() is None:
        raise ValueError('aware as_of required')
    if len(staff_ids) != len(set(staff_ids)):
        raise ValueError('duplicate staff')
    selected = set(staff_ids)
    latest = {}
    seen = set()
    for event in events:
        if event['venue_id'] != venue_id or event['staff_id'] not in selected:
            continue
        if event['source'] != 'kiosk' or event['kind'] not in ('in', 'out'):
            raise ValueError('unsupported attendance event')
        at = event['occurred_at']
        if not isinstance(at, datetime) or at.tzinfo is None or at.utcoffset() is None:
            raise ValueError('aware punch timestamp required')
        if at > as_of:
            continue
        eid = event['event_id']
        if eid in seen:
            raise ValueError('duplicate attendance event')
        seen.add(eid)
        key = event['staff_id']
        rank = (at.astimezone(timezone.utc), str(eid))
        if key not in latest or rank > latest[key][0]:
            latest[key] = (rank, event['kind'])
    return {'venue_id': venue_id, 'as_of': as_of.astimezone(timezone.utc).isoformat(),
            'source': 'trusted_kiosk_events',
            'staff': [{'staff_id': sid,
                       'presence': ('unknown' if sid not in latest else
                                    'clocked_in' if latest[sid][1] == 'in' else 'clocked_out')}
                      for sid in staff_ids]}
