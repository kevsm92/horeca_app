"""Offline venue-scoped lease extension for a long-running mock worker."""
from datetime import datetime, timedelta, timezone


def renew_lease(db, *, venue_id, event_id, lease_token, now, lease_seconds=60):
    """Extend only a live, owned lease; return False for stale or foreign claims.

    Caller must authorize venue_id. No external delivery or employee tracking.
    """
    if not all(isinstance(x, str) and x.strip() for x in (venue_id, event_id, lease_token)):
        raise ValueError('venue, event and token required')
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise ValueError('aware time required')
    if type(lease_seconds) is not int or not 1 <= lease_seconds <= 3600:
        raise ValueError('invalid lease duration')
    if db.in_transaction:
        raise ValueError('unowned transaction required')
    instant = now.astimezone(timezone.utc)
    db.execute('BEGIN IMMEDIATE')
    try:
        updated = db.execute('''UPDATE workflow_outbox SET lease_expires_at_utc=?
            WHERE venue_id=? AND event_id=? AND state='leased' AND lease_token=?
            AND lease_expires_at_utc>?''',
            ((instant + timedelta(seconds=lease_seconds)).isoformat(), venue_id,
             event_id, lease_token, instant.isoformat())).rowcount
        db.commit()
        return updated == 1
    except BaseException:
        db.rollback()
        raise
