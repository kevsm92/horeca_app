"""Offline, pure active-seating conflict guard for reservation allocation.

Not an authorization layer or a substitute for transactional write-time checks.
"""
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class SeatingSession:
    venue_id: str
    table_id: str
    guest_count: int
    started_at: datetime
    ended_at: datetime | None = None


def table_has_active_seating(venue_id: str, table_id: str,
                             sessions: tuple[SeatingSession, ...]) -> bool:
    """Fail closed for invalid same-venue records; ignore other venues entirely."""
    if not isinstance(venue_id, str) or not venue_id.strip():
        raise ValueError('venue required')
    if not isinstance(table_id, str) or not table_id.strip():
        raise ValueError('table required')
    active = False
    for session in sessions:
        if session.venue_id != venue_id:
            continue
        if not session.table_id or type(session.guest_count) is not int or session.guest_count < 1:
            raise ValueError('invalid seating session')
        start = session.started_at
        end = session.ended_at
        if not isinstance(start, datetime) or start.tzinfo is None or start.utcoffset() is None:
            raise ValueError('timezone-aware session start required')
        if end is not None and (not isinstance(end, datetime) or end.tzinfo is None
                                or end.utcoffset() is None or end <= start):
            raise ValueError('invalid session end')
        if session.table_id == table_id and end is None:
            active = True
    return active
