"""Offline SQLite waitlist promotion. Caller MUST authenticate and authorize venue.
Synthetic fixture only; no external notifications, real bookings, or payments.
"""
import sqlite3
from datetime import datetime, timedelta, timezone

class PromotionConflict(ValueError):
    pass

def _utc(value):
    try:
        d = datetime.fromisoformat(value)
        if d.tzinfo is None or d.utcoffset() != timedelta(0):
            raise ValueError
        return d.astimezone(timezone.utc)
    except (TypeError, ValueError, AttributeError):
        raise ValueError("UTC ISO timestamp required") from None

def initialize_promotion_fixture(db):
    db.execute("PRAGMA foreign_keys=ON")
    db.executescript("""
    CREATE TABLE IF NOT EXISTS promotion_tables (
      venue_id TEXT NOT NULL, table_id TEXT NOT NULL,
      capacity INTEGER NOT NULL CHECK(capacity BETWEEN 1 AND 100),
      PRIMARY KEY(venue_id,table_id));
    CREATE TABLE IF NOT EXISTS promotion_waitlist (
      venue_id TEXT NOT NULL, request_id TEXT NOT NULL,
      party_size INTEGER NOT NULL CHECK(party_size BETWEEN 1 AND 100),
      start_utc TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'waiting'
        CHECK(status IN ('waiting','promoted','withdrawn')),
      PRIMARY KEY(venue_id,request_id));
    CREATE TABLE IF NOT EXISTS promotion_bookings (
      venue_id TEXT NOT NULL, booking_id TEXT NOT NULL,
      request_id TEXT NOT NULL, table_id TEXT NOT NULL,
      starts_utc TEXT NOT NULL, ends_utc TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'confirmed' CHECK(status IN ('confirmed','cancelled')),
      PRIMARY KEY(venue_id,booking_id), UNIQUE(venue_id,request_id),
      FOREIGN KEY(venue_id,table_id) REFERENCES promotion_tables(venue_id,table_id));
    CREATE TABLE IF NOT EXISTS promotion_seating (
      venue_id TEXT NOT NULL, table_id TEXT NOT NULL,
      ended_utc TEXT, FOREIGN KEY(venue_id,table_id)
        REFERENCES promotion_tables(venue_id,table_id));
    """)

def promote(db, *, venue_id, request_id, table_id, booking_id,
            duration_minutes, turnover_minutes=0):
    """Atomically promote one waiting request; exact replay returns False.

    Reject active seating, overlapping confirmed booking (including turnover),
    cross-venue table, stale request, or reused booking identifier.
    """
    if any(not isinstance(v, str) or not v.strip() or v != v.strip()
           for v in (venue_id, request_id, table_id, booking_id)):
        raise ValueError("nonempty trimmed identifiers required")
    if (type(duration_minutes) is not int or not 1 <= duration_minutes <= 1440
        or type(turnover_minutes) is not int or not 0 <= turnover_minutes <= 240):
        raise ValueError("invalid duration/turnover")
    if db.in_transaction:
        raise ValueError("cannot nest promotion transaction")
    db.execute("BEGIN IMMEDIATE")
    try:
        previous = db.execute(
            "SELECT request_id,table_id,status FROM promotion_bookings "
            "WHERE venue_id=? AND booking_id=?", (venue_id,booking_id)).fetchone()
        request = db.execute(
            "SELECT party_size,start_utc,status FROM promotion_waitlist "
            "WHERE venue_id=? AND request_id=?", (venue_id,request_id)).fetchone()
        if request is None:
            raise PromotionConflict("request absent in authorized venue")
        party,start_raw,state = request
        start = _utc(start_raw)
        end = start + timedelta(minutes=duration_minutes)
        if previous is not None:
            if previous == (request_id,table_id,"confirmed") and state == "promoted":
                db.commit()
                return False
            raise PromotionConflict("booking identifier already used")
        if state != "waiting":
            raise PromotionConflict("request not waiting")
        table = db.execute("SELECT capacity FROM promotion_tables "
                           "WHERE venue_id=? AND table_id=?", (venue_id,table_id)).fetchone()
        if table is None or table[0] < party:
            raise PromotionConflict("table missing or insufficient physical seats")
        if db.execute("SELECT 1 FROM promotion_seating WHERE venue_id=? "
                      "AND table_id=? AND ended_utc IS NULL LIMIT 1",
                      (venue_id,table_id)).fetchone():
            raise PromotionConflict("table actively seated")
        for other_start,other_end in db.execute(
                "SELECT starts_utc,ends_utc FROM promotion_bookings "
                "WHERE venue_id=? AND table_id=? AND status='confirmed'",
                (venue_id,table_id)):
            a,b = _utc(other_start),_utc(other_end)
            if b <= a:
                raise PromotionConflict("invalid existing booking interval")
            turnover = timedelta(minutes=turnover_minutes)
            if start < b + turnover and a < end + turnover:
                raise PromotionConflict("booking overlap or turnover conflict")
        db.execute("INSERT INTO promotion_bookings "
                   "(venue_id,booking_id,request_id,table_id,starts_utc,ends_utc) "
                   "VALUES (?,?,?,?,?,?)",
                   (venue_id,booking_id,request_id,table_id,start.isoformat(),end.isoformat()))
        changed = db.execute("UPDATE promotion_waitlist SET status='promoted' "
                             "WHERE venue_id=? AND request_id=? AND status='waiting'",
                             (venue_id,request_id)).rowcount
        if changed != 1:
            raise PromotionConflict("stale waitlist status")
        db.commit()
        return True
    except BaseException:
        db.rollback()
        raise
