"""Offline waitlist candidate selection. Advisory only: booking requires transactional
venue, table-capacity, seating-session and overlap revalidation under DB locks.
No notifications, reservations or customer communications are performed.
"""
from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class WaitEntry:
    entry_id: str
    venue_id: str
    guests: int
    requested_at: datetime
    earliest: datetime
    latest: datetime
    status: str = "waiting"

def candidates(entries, *, venue_id: str, available_at: datetime, capacity: int):
    """Stable FIFO eligible entry IDs, without any side effects."""
    if capacity < 1 or not venue_id or available_at.tzinfo is None:
        raise ValueError("capacity, venue and timezone-aware available_at required")
    eligible = []
    for entry in entries:
        if entry.venue_id != venue_id or entry.status != "waiting":
            continue
        if entry.guests < 1 or entry.requested_at.tzinfo is None:
            raise ValueError("invalid waitlist entry")
        if entry.earliest.tzinfo is None or entry.latest.tzinfo is None:
            raise ValueError("timezone-aware window required")
        if entry.earliest <= available_at <= entry.latest and entry.guests <= capacity:
            eligible.append(entry)
    return [e.entry_id for e in sorted(eligible, key=lambda e: (e.requested_at, e.entry_id))]
