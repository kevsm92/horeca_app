"""Offline SQLite reservation cancellation with optimistic revision checks.

Prototype schema: reservations(id, venue_id, status, revision). Caller must
supply an authenticated/authorized venue ID; this function is not an API gate.
"""
import sqlite3


class CancellationConflict(ValueError):
    pass


def cancel_reservation(conn: sqlite3.Connection, *, venue_id: str,
                       reservation_id: str, expected_revision: int) -> int:
    """Cancel a confirmed reservation atomically; return its new revision.

    No implicit commit of caller transactions; require exclusive ownership of
    the supplied connection and an initially inactive transaction.
    """
    if not venue_id or not reservation_id or type(expected_revision) is not int or expected_revision < 0:
        raise ValueError('invalid cancellation input')
    if conn.in_transaction:
        raise ValueError('connection already in transaction')
    conn.execute('BEGIN IMMEDIATE')
    try:
        cur = conn.execute(
            "UPDATE reservations SET status='cancelled', revision=revision+1 "
            "WHERE id=? AND venue_id=? AND status='confirmed' AND revision=?",
            (reservation_id, venue_id, expected_revision),
        )
        if cur.rowcount != 1:
            raise CancellationConflict('not found, stale, or non-cancellable')
        conn.commit()
        return expected_revision + 1
    except BaseException:
        conn.rollback()
        raise
