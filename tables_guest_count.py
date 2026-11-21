"""Venue-scoped active seating guest-count correction (offline SQLite prototype).

Caller must authorize venue_id; this module is not an authentication boundary.
"""


def set_active_guest_count(db, venue_id, session_id, guests):
    """Update an active session without changing its identity or exceeding capacity.

    SQLite schema triggers enforce capacity atomically, including concurrent writes.
    """
    if not isinstance(venue_id, str) or not venue_id.strip():
        raise ValueError("nonempty venue_id required")
    if not isinstance(session_id, str) or not session_id.strip():
        raise ValueError("nonempty session_id required")
    if type(guests) is not int or guests <= 0:
        raise ValueError("guests must be a positive integer")
    with db:
        result = db.execute(
            "UPDATE seating_sessions SET guest_count=? "
            "WHERE venue_id=? AND session_id=? AND status='active'",
            (guests, venue_id, session_id),
        )
        if result.rowcount != 1:
            raise ValueError("active seating session not found in venue")
