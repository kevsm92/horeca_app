"""Offline dead-letter review; caller must authorize venue manager access."""


def list_dead_letters(db, *, venue_id, limit=25, before_event_id=None):
    """Return stable, bounded event metadata, never payloads or lease tokens.

    Cursor pagination uses event ID order (not occurrence chronology).
    """
    if not isinstance(venue_id, str) or not venue_id.strip():
        raise ValueError('venue required')
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError('limit must be 1..100')
    if before_event_id is not None and (not isinstance(before_event_id, str) or not before_event_id.strip()):
        raise ValueError('invalid cursor')
    rows = db.execute("""SELECT event_id,event_type,attempt_count,last_error_code
        FROM workflow_outbox WHERE venue_id=? AND state='dead_letter'
        AND (? IS NULL OR event_id < ?)
        ORDER BY event_id DESC LIMIT ?""",
        (venue_id, before_event_id, before_event_id, limit + 1)).fetchall()
    has_more = len(rows) > limit
    page = rows[:limit]
    return {'items': [dict(zip(('event_id','event_type','attempt_count','last_error_code'), r))
                      for r in page],
            'next_cursor': page[-1][0] if has_more else None}
