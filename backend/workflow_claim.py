"""Venue-scoped offline outbox leasing; never invokes external handlers."""
from datetime import datetime, timedelta, timezone
from uuid import uuid4


def claim_due(db, *, venue_id, now, lease_seconds=60):
    """Atomically lease one due event for an authorized venue; caller commits."""
    if not isinstance(venue_id, str) or not venue_id.strip():
        raise ValueError('venue required')
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError('aware time required')
    if type(lease_seconds) is not int or not 1 <= lease_seconds <= 3600:
        raise ValueError('invalid lease duration')
    if db.in_transaction:
        raise ValueError('claim requires unowned transaction')
    instant = now.astimezone(timezone.utc)
    timestamp = instant.isoformat()
    db.execute('BEGIN IMMEDIATE')
    try:
        row = db.execute("""SELECT event_id,event_type,payload_json FROM workflow_outbox
            WHERE venue_id=? AND available_at_utc<=? AND
            (state='pending' OR (state='leased' AND lease_expires_at_utc<=?))
            ORDER BY available_at_utc,event_id LIMIT 1""",
            (venue_id,timestamp,timestamp)).fetchone()
        if row is None:
            db.commit()
            return None
        token = str(uuid4())
        expiry = (instant + timedelta(seconds=lease_seconds)).isoformat()
        db.execute("""UPDATE workflow_outbox SET state='leased',lease_token=?,
            lease_expires_at_utc=?,attempt_count=attempt_count+1
            WHERE event_id=? AND venue_id=?""", (token,expiry,row[0],venue_id))
        db.commit()
        return {'event_id':row[0], 'event_type':row[1], 'payload_json':row[2],
                'lease_token':token, 'lease_expires_at_utc':expiry}
    except BaseException:
        db.rollback()
        raise
