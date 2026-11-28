"""Read-only, venue-scoped waitlist candidate ranking for offline staff review.

The caller must authenticate/authorize the venue and supply trustworthy physical
capacity. A candidate is not a reservation, offer, or guarantee of availability.
"""
import sqlite3
from datetime import datetime, timezone


def rank_candidates(conn: sqlite3.Connection, *, venue_id: str, available_seats: int,
                    not_after_utc: str, limit: int = 20) -> list[dict]:
    """Return waiting requests fitting one physical table, oldest request first.

    Stable ties use request_id. All comparisons are UTC timestamps, never text
    ordering; no mutation, reservation, guest contact, or table lock occurs.
    """
    if not isinstance(venue_id, str) or not venue_id.strip():
        raise ValueError('venue required')
    if type(available_seats) is not int or not 1 <= available_seats <= 100:
        raise ValueError('invalid available seats')
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError('invalid limit')
    try:
        cutoff = datetime.fromisoformat(not_after_utc)
        if cutoff.tzinfo is None or cutoff.utcoffset() is None or cutoff.utcoffset().total_seconds() != 0:
            raise ValueError
        cutoff = cutoff.astimezone(timezone.utc)
    except (TypeError, ValueError, AttributeError):
        raise ValueError('not_after_utc must be UTC ISO datetime') from None
    rows = conn.execute(
        "SELECT request_id,party_size,start_utc FROM reservation_waitlist "
        "WHERE venue_id=? AND status='waiting' AND party_size<=?",
        (venue_id, available_seats),
    ).fetchall()
    eligible = []
    for request_id, party_size, start_utc in rows:
        timestamp = datetime.fromisoformat(start_utc).astimezone(timezone.utc)
        if timestamp <= cutoff:
            eligible.append((timestamp, request_id, party_size))
    eligible.sort(key=lambda r: (r[0], r[1]))
    return [dict(request_id=request_id, party_size=party_size,
                 start_utc=timestamp.isoformat())
            for timestamp, request_id, party_size in eligible[:limit]]
