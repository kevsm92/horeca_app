"""Read-only, venue-scoped occupancy projection for the offline SQLite prototype.

Caller must authenticate and authorize venue_id; this is not an auth boundary.
Corrupt active seating must fail closed, not appear as an available table.
"""


def occupancy_for_venue(db, venue_id):
    """Return (table_id, capacity, status, guests, session_id), ordered by ID."""
    if not isinstance(venue_id, str) or not venue_id.strip():
        raise ValueError("nonempty venue_id required")
    orphan = db.execute(
        "SELECT 1 FROM seating_sessions s LEFT JOIN physical_tables t "
        "ON t.venue_id=s.venue_id AND t.table_id=s.table_id "
        "WHERE s.venue_id=? AND s.status='active' AND t.table_id IS NULL LIMIT 1",
        (venue_id,),
    ).fetchone()
    if orphan:
        raise ValueError("active seating references missing physical table")
    rows = db.execute(
        "SELECT t.table_id, t.capacity, s.session_id, s.guest_count "
        "FROM physical_tables t LEFT JOIN seating_sessions s "
        "ON s.venue_id=t.venue_id AND s.table_id=t.table_id AND s.status='active' "
        "WHERE t.venue_id=? ORDER BY t.table_id", (venue_id,)
    ).fetchall()
    result = []
    seen = set()
    for table_id, capacity, session_id, guests in rows:
        if table_id in seen:
            raise ValueError("duplicate active seating or physical table")
        seen.add(table_id)
        if type(capacity) is not int or capacity < 1:
            raise ValueError("invalid physical capacity")
        if session_id is not None and (type(guests) is not int or not 1 <= guests <= capacity):
            raise ValueError("invalid active guest count")
        result.append((table_id, capacity, 'occupied' if session_id is not None else 'available',
                       guests if session_id is not None else 0, session_id))
    return result
