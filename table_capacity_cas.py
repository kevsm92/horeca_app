"""Atomic, venue-scoped capacity change for the existing SQLite table prototype.

Caller must authorize the venue separately. This does not change immutable
physical inventory or persist visual dimensions.
"""
import sqlite3


def change_table_capacity(db: sqlite3.Connection, venue_id: str, table_id: str,
                          expected_capacity: int, requested_capacity: int) -> None:
    """Compare-and-swap capacity, rechecking occupancy in a write transaction."""
    if db.in_transaction:
        raise ValueError("capacity change requires no active transaction")
    if not isinstance(venue_id, str) or not venue_id or not isinstance(table_id, str) or not table_id:
        raise ValueError("venue and table identifiers required")
    if type(expected_capacity) is not int or type(requested_capacity) is not int:
        raise ValueError("capacity values must be integers")
    if not 1 <= expected_capacity <= 100 or not 1 <= requested_capacity <= 100:
        raise ValueError("capacity outside physical table limits")
    db.execute("BEGIN IMMEDIATE")
    try:
        result = db.execute(
            "UPDATE physical_tables SET capacity=? WHERE venue_id=? AND table_id=? "
            "AND capacity=? AND NOT EXISTS ("
            "SELECT 1 FROM seating_sessions WHERE venue_id=? AND table_id=? "
            "AND status='active' AND guest_count>?)",
            (requested_capacity, venue_id, table_id, expected_capacity,
             venue_id, table_id, requested_capacity))
        if result.rowcount != 1:
            raise ValueError("table missing, stale capacity, or occupied above requested capacity")
        db.execute("COMMIT")
    except BaseException:
        db.execute("ROLLBACK")
        raise
