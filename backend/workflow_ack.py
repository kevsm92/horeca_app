"""Offline venue-scoped acknowledgement of a leased outbox event."""
from datetime import datetime, timezone


def acknowledge(db, *, venue_id, event_id, lease_token, now):
    """Mark a currently owned, unexpired lease delivered; never dispatches."""
    if not all(isinstance(x, str) and x.strip() for x in (venue_id, event_id, lease_token)):
        raise ValueError('nonempty lease identity required')
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise ValueError('aware datetime required')
    if db.in_transaction:
        raise ValueError('unowned transaction required')
    instant = now.astimezone(timezone.utc).isoformat()
    db.execute('BEGIN IMMEDIATE')
    try:
        updated = db.execute("""UPDATE workflow_outbox SET state='delivered',
            lease_token=NULL, lease_expires_at_utc=NULL, last_error_code=NULL
            WHERE venue_id=? AND event_id=? AND lease_token=? AND state='leased'
            AND lease_expires_at_utc>?""",
            (venue_id, event_id, lease_token, instant)).rowcount
        db.commit()
        return updated == 1
    except BaseException:
        db.rollback()
        raise
