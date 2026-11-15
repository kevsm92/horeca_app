"""Offline reservation waitlist enrollment; no guest messages or personal data.

Caller supplies an authorized venue scope. This is not an authentication layer.
Enrollment does not promise a table or confirmed booking.
"""
import sqlite3
from datetime import datetime, timezone


class WaitlistConflict(ValueError):
    pass


def initialize_waitlist(conn: sqlite3.Connection) -> None:
    conn.execute("""CREATE TABLE IF NOT EXISTS reservation_waitlist (
        venue_id TEXT NOT NULL, request_id TEXT NOT NULL,
        party_size INTEGER NOT NULL CHECK(party_size > 0),
        start_utc TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'waiting'
            CHECK(status IN ('waiting', 'withdrawn')),
        PRIMARY KEY(venue_id, request_id))""")


def enroll(conn: sqlite3.Connection, *, venue_id: str, request_id: str,
           party_size: int, start_utc: str) -> bool:
    """Insert once; exact replay returns False; mismatched replay conflicts."""
    if not isinstance(venue_id, str) or not venue_id.strip() or not isinstance(request_id, str) or not request_id.strip():
        raise ValueError('venue and request required')
    if type(party_size) is not int or party_size < 1 or party_size > 100:
        raise ValueError('invalid party size')
    try:
        parsed = datetime.fromisoformat(start_utc)
        if parsed.tzinfo is None or parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
            raise ValueError
        normalized = parsed.astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError, AttributeError):
        raise ValueError('start_utc must be UTC ISO datetime') from None
    if conn.in_transaction:
        raise ValueError('connection already in transaction')
    conn.execute('BEGIN IMMEDIATE')
    try:
        row = conn.execute('SELECT party_size,start_utc,status FROM reservation_waitlist WHERE venue_id=? AND request_id=?',
                           (venue_id, request_id)).fetchone()
        if row:
            if row != (party_size, normalized, 'waiting'):
                raise WaitlistConflict('request id already used or withdrawn')
            conn.commit()
            return False
        conn.execute('INSERT INTO reservation_waitlist(venue_id,request_id,party_size,start_utc) VALUES(?,?,?,?)',
                     (venue_id, request_id, party_size, normalized))
        conn.commit()
        return True
    except BaseException:
        conn.rollback()
        raise
