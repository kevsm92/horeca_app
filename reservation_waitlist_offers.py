"""Offline provisional waitlist offers; no booking, guest contact, or table assignment.

Caller must authorize venue_id and verify physical table ownership/capacity.
Offers are only staff-review holds; reservation admission must recheck conflicts.
"""
import sqlite3
from datetime import datetime, timezone


class OfferConflict(ValueError):
    pass


def _utc(value):
    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None or dt.utcoffset() is None or dt.utcoffset().total_seconds() != 0:
            raise ValueError
        return dt.astimezone(timezone.utc)
    except (TypeError, ValueError, AttributeError):
        raise ValueError("UTC ISO timestamp required") from None


def initialize_offers(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS waitlist_offers (
        venue_id TEXT NOT NULL, offer_id TEXT NOT NULL,
        request_id TEXT NOT NULL, table_id TEXT NOT NULL,
        created_utc TEXT NOT NULL, expires_utc TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'offered'
            CHECK(status IN ('offered','expired','declined')),
        PRIMARY KEY (venue_id, offer_id),
        FOREIGN KEY (venue_id, request_id)
            REFERENCES reservation_waitlist(venue_id, request_id)
    )""")
    conn.execute("""CREATE INDEX IF NOT EXISTS waitlist_offers_table_idx
        ON waitlist_offers(venue_id,table_id,status,expires_utc)""")


def create_offer(conn, *, venue_id, offer_id, request_id, table_id,
                 created_utc, expires_utc):
    """Create one provisional offer, rejecting overlapping active holds.

    This does NOT establish that a table is free of confirmed reservations or
    seating. The caller must check those in the same transaction before using
    this as a real reservation admission workflow.
    """
    if any(not isinstance(v, str) or not v.strip()
           for v in (venue_id, offer_id, request_id, table_id)):
        raise ValueError("nonempty venue, offer, request and table required")
    created, expires = _utc(created_utc), _utc(expires_utc)
    if expires <= created:
        raise ValueError("expiry must be after creation")
    if conn.in_transaction:
        raise ValueError("connection already in transaction")
    conn.execute("BEGIN IMMEDIATE")
    try:
        previous = conn.execute(
            "SELECT request_id,table_id,created_utc,expires_utc,status "
            "FROM waitlist_offers WHERE venue_id=? AND offer_id=?",
            (venue_id, offer_id)).fetchone()
        expected = (request_id, table_id, created.isoformat(), expires.isoformat(), 'offered')
        if previous is not None:
            if previous != expected:
                raise OfferConflict("offer ID already used or changed")
            conn.commit()
            return False
        waiting = conn.execute(
            "SELECT 1 FROM reservation_waitlist "
            "WHERE venue_id=? AND request_id=? AND status='waiting'",
            (venue_id, request_id)).fetchone()
        if waiting is None:
            raise OfferConflict("request not waiting in authorized venue")
        # Fractional-second UTC ISO strings are not always lexicographically
        # time-ordered (e.g. 18:15:00.5 vs 18:15:00+00:00).
        # Compare parsed instants under the BEGIN IMMEDIATE writer lock.
        candidates = conn.execute(
            "SELECT expires_utc FROM waitlist_offers "
            "WHERE venue_id=? AND status='offered' "
            "AND (table_id=? OR request_id=?)",
            (venue_id, table_id, request_id)).fetchall()
        if any(_utc(row[0]) > created for row in candidates):
            raise OfferConflict("active table or request offer exists")
        conn.execute(
            "INSERT INTO waitlist_offers "
            "(venue_id,offer_id,request_id,table_id,created_utc,expires_utc) "
            "VALUES(?,?,?,?,?,?)",
            (venue_id, offer_id, request_id, table_id,
             created.isoformat(), expires.isoformat()))
        conn.commit()
        return True
    except BaseException:
        conn.rollback()
        raise
