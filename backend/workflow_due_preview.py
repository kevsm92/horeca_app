"""Read-only offline due-event preview; venue authorization is the caller's duty.

This is a bounded operational preview, not a worker or network dispatcher.
"""
from datetime import datetime, timezone


def preview_due(db, *, venue_id, now, limit=20):
    """Return oldest actionable event metadata without payload or lease credentials."""
    if not isinstance(venue_id, str) or not venue_id.strip():
        raise ValueError('venue required')
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise ValueError('aware datetime required')
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError('limit must be between 1 and 100')
    instant = now.astimezone(timezone.utc).isoformat()
    rows = db.execute("""SELECT event_id, event_type, available_at_utc, attempt_count,
            CASE WHEN state='leased' THEN 'expired_lease' ELSE 'pending' END
        FROM workflow_outbox
        WHERE venue_id=? AND available_at_utc<=?
          AND (state='pending' OR (state='leased' AND lease_expires_at_utc<=?))
        ORDER BY available_at_utc,event_id LIMIT ?""",
        (venue_id, instant, instant, limit)).fetchall()
    return [{'event_id': event_id, 'event_type': event_type,
             'available_at_utc': available_at, 'attempt_count': attempts,
             'reason': reason}
            for event_id, event_type, available_at, attempts, reason in rows]
