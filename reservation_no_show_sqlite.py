"""Offline, staff-confirmed reservation no-show CAS. Caller authorizes venue and verifies schedule."""
from datetime import datetime, timedelta, timezone

class NoShowConflict(ValueError):
    pass

def _utc(value):
    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None or dt.utcoffset() is None or dt.utcoffset().total_seconds() != 0:
            raise ValueError
        return dt.astimezone(timezone.utc)
    except (TypeError, ValueError, AttributeError):
        raise ValueError("UTC ISO timestamp required") from None

def mark_no_show(conn, *, venue_id, reservation_id, expected_revision,
                 scheduled_utc, now_utc, grace_minutes, staff_confirmed):
    """Confirmed -> no_show only after grace and explicit staff confirmation.

    scheduled_utc must match the persisted booking under the write lock.
    Schema must permit no_show status; this function does not migrate it.
    """
    if any(not isinstance(v, str) or not v.strip() for v in (venue_id, reservation_id)):
        raise ValueError("venue and reservation required")
    if type(expected_revision) is not int or expected_revision < 0:
        raise ValueError("invalid revision")
    if type(grace_minutes) is not int or not 0 <= grace_minutes <= 1440:
        raise ValueError("invalid grace")
    if staff_confirmed is not True:
        raise NoShowConflict("staff confirmation required")
    scheduled = _utc(scheduled_utc)
    now = _utc(now_utc)
    if conn.in_transaction:
        raise ValueError("connection already in transaction")
    conn.execute("BEGIN IMMEDIATE")
    try:
        row = conn.execute("SELECT scheduled_utc FROM reservations WHERE id=? AND venue_id=? AND status='confirmed' AND revision=?", (reservation_id, venue_id, expected_revision)).fetchone()
        if row is None:
            raise NoShowConflict("not found, stale or non-confirmed")
        try:
            persisted = _utc(row[0])
        except ValueError:
            raise NoShowConflict("invalid persisted schedule") from None
        if persisted != scheduled:
            raise NoShowConflict("stale booking schedule")
        if now < persisted + timedelta(minutes=grace_minutes):
            raise NoShowConflict("grace period not elapsed")
        cur = conn.execute(
            "UPDATE reservations SET status='no_show', revision=revision+1 "
            "WHERE id=? AND venue_id=? AND status='confirmed' AND revision=?",
            (reservation_id, venue_id, expected_revision))
        if cur.rowcount != 1:
            raise NoShowConflict("not found, stale or non-confirmed")
        conn.commit()
        return expected_revision + 1
    except BaseException:
        conn.rollback()
        raise
