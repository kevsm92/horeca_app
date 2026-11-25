"""Offline manager-facing requeue audit metadata; caller authorizes venue access."""


def list_requeue_history(db, *, venue_id, limit=25, before_id=None):
    """Page immutable recovery records by descending audit ID, without event payloads."""
    if not isinstance(venue_id, str) or not venue_id.strip():
        raise ValueError('venue required')
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError('limit must be 1..100')
    if before_id is not None and (type(before_id) is not int or before_id < 1):
        raise ValueError('invalid cursor')
    rows = db.execute('''SELECT id,event_id,manager_id,requeued_at_utc
        FROM workflow_dead_letter_requeues WHERE venue_id=?
        AND (? IS NULL OR id < ?) ORDER BY id DESC LIMIT ?''',
        (venue_id, before_id, before_id, limit + 1)).fetchall()
    page = rows[:limit]
    return {
        'items': [dict(zip(('id','event_id','manager_id','requeued_at_utc'), row)) for row in page],
        'next_cursor': page[-1][0] if len(rows) > limit else None,
    }
