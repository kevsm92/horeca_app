"""Offline atomic reservation modification prototype; caller supplies authorized venue.
Expected schema: tables(venue,id,capacity), bookings(venue,id,table_id,party,
start_us,end_us,turnover_us,status,revision). Not an API authorization layer.
"""
import sqlite3

class ModificationConflict(ValueError):
    pass

def modify_reservation(conn: sqlite3.Connection, *, venue: str, booking_id: str,
                       expected_revision: int, table_id: str, party: int,
                       start_us: int, end_us: int, turnover_us: int) -> int:
    if not all(type(v) is str and v.strip() for v in (venue, booking_id, table_id)):
        raise ValueError('invalid identifier')
    if any(type(v) is not int for v in (expected_revision, party, start_us, end_us, turnover_us)):
        raise ValueError('integer fields required')
    if expected_revision < 0 or party < 1 or start_us < 0 or end_us <= start_us or turnover_us < 0:
        raise ValueError('invalid revision, party, or time range')
    if conn.in_transaction:
        raise ValueError('connection already in transaction')
    conn.execute('BEGIN IMMEDIATE')
    try:
        current = conn.execute('SELECT status, revision FROM bookings WHERE venue=? AND id=?',
                               (venue, booking_id)).fetchone()
        if current != ('confirmed', expected_revision):
            raise ModificationConflict('missing, non-modifiable, or stale booking')
        capacity = conn.execute('SELECT capacity FROM tables WHERE venue=? AND id=?',
                                (venue, table_id)).fetchone()
        if capacity is None or type(capacity[0]) is not int or capacity[0] < party:
            raise ModificationConflict('table unavailable or insufficient capacity')
        overlap = conn.execute("""SELECT 1 FROM bookings WHERE venue=? AND table_id=?
            AND id<>? AND status IN ('confirmed','seated')
            AND ? < end_us + turnover_us AND start_us < ? LIMIT 1""",
            (venue, table_id, booking_id, start_us, end_us + turnover_us)).fetchone()
        if overlap:
            raise ModificationConflict('time overlap including turnover')
        updated = conn.execute("""UPDATE bookings SET table_id=?,party=?,start_us=?,end_us=?,
            turnover_us=?,revision=revision+1 WHERE venue=? AND id=? AND revision=?
            AND status='confirmed' """,
            (table_id, party, start_us, end_us, turnover_us, venue, booking_id, expected_revision))
        if updated.rowcount != 1:
            raise ModificationConflict('concurrent revision change')
        conn.commit()
        return expected_revision + 1
    except BaseException:
        conn.rollback()
        raise
