"""Atomic cancellation for the shared offline bookings schema.

Caller must already have authorized the venue; this is not an HTTP endpoint.
The cancelled row remains for audit/history and no guest is contacted.
"""
import sqlite3


class BookingCancellationConflict(ValueError):
    """Booking absent, stale, or not cancellable."""


def cancel_booking(conn: sqlite3.Connection, *, venue: str, booking_id: str,
                   expected_revision: int) -> int:
    if not all(type(s) is str and s.strip() for s in (venue, booking_id)):
        raise ValueError('venue and booking ID required')
    if type(expected_revision) is not int or expected_revision < 0:
        raise ValueError('nonnegative integer revision required')
    if conn.in_transaction:
        raise ValueError('connection already in transaction')
    conn.execute('BEGIN IMMEDIATE')
    try:
        changed = conn.execute(
            "UPDATE bookings SET status='cancelled', revision=revision+1 "
            "WHERE venue=? AND id=? AND status='confirmed' AND revision=?",
            (venue, booking_id, expected_revision),
        )
        if changed.rowcount != 1:
            raise BookingCancellationConflict('missing, stale or non-cancellable booking')
        conn.commit()
        return expected_revision + 1
    except BaseException:
        conn.rollback()
        raise
