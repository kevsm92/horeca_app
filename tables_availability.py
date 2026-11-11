"""Venue-scoped physical table availability read model (offline SQLite prototype).

The caller must authorize venue_id before calling; this is not an API boundary.
"""


def list_table_availability(db, venue_id):
    """Return physical inventory with active occupancy; no synthetic empty tables.

    Rows: (table_id, capacity, occupied_guests, available_seats, status).
    A table is unavailable for a new seating if *any* active session exists,
    regardless of spare seats. Do not confuse available_seats with seatability.
    """
    if not isinstance(venue_id, str) or not venue_id.strip():
        raise ValueError('nonempty venue_id required')
    rows = db.execute(
        "SELECT t.table_id, t.capacity, s.guest_count "
        "FROM physical_tables AS t "
        "LEFT JOIN seating_sessions AS s "
        "ON s.venue_id=t.venue_id AND s.table_id=t.table_id AND s.status='active' "
        "WHERE t.venue_id=? ORDER BY t.table_id", (venue_id,)
    ).fetchall()
    return [(table_id, capacity, guests or 0, capacity - (guests or 0),
             'occupied' if guests is not None else 'vacant')
            for table_id, capacity, guests in rows]
