"""Read-only, venue-scoped operational outbox event lookup (offline only).

Caller must authenticate and authorize the venue before invoking this function.
Never exposes payloads or lease tokens to dashboard consumers.
"""

def lookup_event(db, *, venue_id, event_id):
    if not isinstance(venue_id, str) or not venue_id.strip():
        raise ValueError('venue required')
    if not isinstance(event_id, str) or not event_id.strip():
        raise ValueError('event id required')
    row = db.execute('''SELECT event_id,event_type,event_version,aggregate_id,
        aggregate_revision,created_at_utc,available_at_utc,attempt_count,state,
        lease_expires_at_utc,last_error_code FROM workflow_outbox
        WHERE venue_id=? AND event_id=?''', (venue_id,event_id)).fetchone()
    if row is None:
        return None
    keys = ('event_id','event_type','event_version','aggregate_id',
            'aggregate_revision','created_at_utc','available_at_utc',
            'attempt_count','state','lease_expires_at_utc','last_error_code')
    return dict(zip(keys,row))
