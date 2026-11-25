"""Offline transactional task projection and outbox acknowledgement.

Caller must authorize venue_id. No network dispatch or real staff/customer data.
"""
from datetime import datetime, timezone

from workflow_task_trigger import project_check_due


def deliver_check_due(db, *, venue_id, event, lease_token, now):
    """Atomically project an owned event and acknowledge its live lease.

    Returns False for stale/wrong leases, True for successful (including replayed)
    projection. A projection exception rolls back both changes.
    """
    if not isinstance(venue_id, str) or not venue_id.strip():
        raise ValueError('venue required')
    if not isinstance(lease_token, str) or not lease_token.strip():
        raise ValueError('lease token required')
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise ValueError('aware time required')
    if not isinstance(event, dict) or not isinstance(event.get('event_id'), str):
        raise ValueError('event id required')
    if db.in_transaction:
        raise ValueError('unowned transaction required')
    instant = now.astimezone(timezone.utc).isoformat()
    db.execute('BEGIN IMMEDIATE')
    try:
        owned = db.execute('''SELECT 1 FROM workflow_outbox
            WHERE event_id=? AND venue_id=? AND state='leased'
            AND lease_token=? AND lease_expires_at_utc>?''',
            (event['event_id'], venue_id, lease_token, instant)).fetchone()
        if owned is None:
            db.commit()
            return False
        project_check_due(db, venue_id=venue_id, event=event)
        updated = db.execute('''UPDATE workflow_outbox SET state='delivered',
            lease_token=NULL, lease_expires_at_utc=NULL, last_error_code=NULL
            WHERE event_id=? AND venue_id=? AND state='leased' AND lease_token=?
            AND lease_expires_at_utc>?''',
            (event['event_id'], venue_id, lease_token, instant)).rowcount
        if updated != 1:
            raise RuntimeError('lease ownership changed')
        db.commit()
        return True
    except BaseException:
        db.rollback()
        raise
