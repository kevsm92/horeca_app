"""Offline venue-scoped manual recovery of dead-lettered outbox events.

Caller must authenticate and authorize a manager for venue_id. No dispatch occurs.
"""
from datetime import datetime, timezone


def requeue_dead_letter(db, *, venue_id, event_id, manager_id, now):
    """Requeue one dead letter with an immutable audit row; return False if ineligible."""
    if not all(isinstance(x, str) and x.strip() for x in (venue_id, event_id, manager_id)):
        raise ValueError('nonempty identifiers required')
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise ValueError('aware datetime required')
    if db.in_transaction:
        raise ValueError('unowned transaction required')
    instant = now.astimezone(timezone.utc).isoformat()
    db.execute('BEGIN IMMEDIATE')
    try:
        changed = db.execute("""UPDATE workflow_outbox SET state='pending',
            available_at_utc=?, attempt_count=0, lease_token=NULL,
            lease_expires_at_utc=NULL, last_error_code=NULL
            WHERE venue_id=? AND event_id=? AND state='dead_letter' """,
            (instant, venue_id, event_id)).rowcount
        if changed:
            db.execute("""INSERT INTO workflow_dead_letter_requeues
                (venue_id,event_id,manager_id,requeued_at_utc)
                VALUES (?,?,?,?)""", (venue_id,event_id,manager_id,instant))
        db.commit()
        return changed == 1
    except BaseException:
        db.rollback()
        raise


def initialize(db):
    db.execute("""CREATE TABLE IF NOT EXISTS workflow_dead_letter_requeues (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        venue_id TEXT NOT NULL, event_id TEXT NOT NULL,
        manager_id TEXT NOT NULL, requeued_at_utc TEXT NOT NULL
    )""")
