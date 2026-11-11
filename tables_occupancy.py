"""Read-only, venue-scoped table occupancy projection for the offline SQLite prototype.

This is not an authorization boundary: callers must authenticate and authorize venue_id.
"""


def occupancy_for_venue(db, venue_id):
    """Return physical inventory with current guests; never expose other venues.

    Each result is (table_id, capacity, status, guests, session_id). The database
    partial unique index ensures at most one active session per physical table.
    """
    if not isinstance(venue_id, str) or not venue_id.strip():
        raise ValueError("nonempty venue_id required")
    rows = db.execute(
        "SELECT t.table_id, t.capacity, "
        "CASE WHEN s.session_id IS NULL THEN 'available' ELSE 'occupied' END, "
        "COALESCE(s.guest_count, 0), s.session_id "
        "FROM physical_tables AS t LEFT JOIN seating_sessions AS s "
        "ON s.venue_id=t.venue_id AND s.table_id=t.table_id AND s.status='active' "
        "WHERE t.venue_id=? ORDER BY t.table_id", (venue_id,)
    ).fetchall()
    return rows
