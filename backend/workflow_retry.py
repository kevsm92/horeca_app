"""Offline outbox negative acknowledgement with bounded retry and dead-letter."""
from datetime import datetime, timedelta, timezone


def fail_lease(db, *, venue_id, event_id, lease_token, now, error_code, max_attempts=3):
    """Release an owned lease for retry, or dead-letter at the attempt limit.

    Caller is responsible for venue authorization; never dispatches or logs payloads.
    Returns 'pending', 'dead_letter', or None for stale/wrong leases.
    """
    if not all(isinstance(v, str) and v.strip() for v in (venue_id, event_id, lease_token)):
        raise ValueError('nonempty lease identity required')
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise ValueError('aware datetime required')
    if error_code not in ('handler_transient', 'handler_rejected', 'internal_error'):
        raise ValueError('unsupported safe error code')
    if type(max_attempts) is not int or not 1 <= max_attempts <= 20:
        raise ValueError('invalid attempt limit')
    if db.in_transaction:
        raise ValueError('unowned transaction required')
    instant = now.astimezone(timezone.utc)
    db.execute('BEGIN IMMEDIATE')
    try:
        row = db.execute("""SELECT attempt_count FROM workflow_outbox
            WHERE venue_id=? AND event_id=? AND lease_token=? AND state='leased'
              AND lease_expires_at_utc>?""",
            (venue_id, event_id, lease_token, instant.isoformat())).fetchone()
        if row is None:
            db.commit()
            return None
        attempts = row[0]
        state = 'dead_letter' if attempts >= max_attempts or error_code == 'handler_rejected' else 'pending'
        delay = min(3600, 30 * 2 ** min(attempts - 1, 7))
        available = (instant + timedelta(seconds=delay)).isoformat()
        db.execute("""UPDATE workflow_outbox SET state=?, available_at_utc=?,
            lease_token=NULL, lease_expires_at_utc=NULL, last_error_code=?
            WHERE venue_id=? AND event_id=? AND lease_token=?""",
            (state, available, error_code, venue_id, event_id, lease_token))
        db.commit()
        return state
    except BaseException:
        db.rollback()
        raise
