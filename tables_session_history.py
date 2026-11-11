"""Venue-scoped, read-only seating history; caller must authorize venue access."""

def list_session_history(db, venue_id, table_id, limit=50, offset=0):
    """Return deterministic session records, including closed sessions, for one physical table."""
    if not isinstance(venue_id, str) or not venue_id.strip():
        raise ValueError('venue_id required')
    if not isinstance(table_id, str) or not table_id.strip():
        raise ValueError('table_id required')
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError('limit must be an integer between 1 and 100')
    if type(offset) is not int or offset < 0:
        raise ValueError('offset must be a nonnegative integer')
    rows = db.execute(
        'SELECT session_id, guest_count, status FROM seating_sessions '
        'WHERE venue_id=? AND table_id=? ORDER BY rowid DESC LIMIT ? OFFSET ?',
        (venue_id, table_id, limit, offset),
    ).fetchall()
    return [dict(session_id=s, guest_count=n, status=state) for s, n, state in rows]
