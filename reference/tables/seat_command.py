"""Offline transactional SQLite Seat command; caller must authorize venue first."""
import sqlite3

class SeatRejected(ValueError):
    pass

def seat(conn: sqlite3.Connection, *, venue_id: str, table_id: str,
         session_id: str, guests: int) -> None:
    """Seat in a pre-authorized venue. No authentication is implemented here."""
    if not all(isinstance(x, str) and x.strip() for x in (venue_id, table_id, session_id)):
        raise SeatRejected("identifiers required")
    if type(guests) is not int or guests < 1:
        raise SeatRejected("positive integer guests required")
    if conn.in_transaction:
        raise SeatRejected("connection already in transaction")
    try:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT capacity_seats,active FROM physical_tables WHERE venue_id=? AND table_id=?",
            (venue_id, table_id)).fetchone()
        if row is None or row[1] != 1:
            raise SeatRejected("table missing or inactive")
        if guests > row[0]:
            raise SeatRejected("over capacity")
        conn.execute(
            "INSERT INTO seating_sessions(venue_id,session_id,table_id,guest_count,state)"
            " VALUES (?,?,?,?, 'active')", (venue_id,session_id,table_id,guests))
        conn.commit()
    except sqlite3.IntegrityError as exc:
        conn.rollback()
        raise SeatRejected("table occupied or session duplicate") from exc
    except BaseException:
        conn.rollback()
        raise
