"""Offline reservation table availability reference; not a concurrency-safe booking service."""
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass(frozen=True)
class Table:
    venue_id: str
    table_id: str
    seats: int

@dataclass(frozen=True)
class Booking:
    venue_id: str
    table_id: str
    starts_at: datetime
    ends_at: datetime
    status: str = "confirmed"

def available_tables(venue_id: str, party_size: int, starts_at: datetime,
                     ends_at: datetime, turnover_minutes: int,
                     tables: list[Table], bookings: list[Booking]) -> list[str]:
    """Half-open reservation windows; cancelled bookings release capacity."""
    if not venue_id or type(party_size) is not int or party_size < 1:
        raise ValueError("valid venue and positive party size required")
    if type(turnover_minutes) is not int or not 0 <= turnover_minutes <= 1440:
        raise ValueError("invalid turnover")
    if (starts_at.tzinfo is None or ends_at.tzinfo is None or
            starts_at.utcoffset() is None or ends_at.utcoffset() is None or
            starts_at >= ends_at):
        raise ValueError("timezone-aware positive interval required")
    if any(t.venue_id == venue_id and t.seats < 1 for t in tables):
        raise ValueError("invalid physical table capacity")
    ids = [t.table_id for t in tables if t.venue_id == venue_id and t.seats >= party_size]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate venue table identifiers")
    for booking in bookings:
        if booking.venue_id != venue_id or booking.status == "cancelled":
            continue
        if booking.status not in ("confirmed", "seated"):
            raise ValueError("unknown booking state")
        if (booking.starts_at.tzinfo is None or booking.ends_at.tzinfo is None or
                booking.starts_at.utcoffset() is None or booking.ends_at.utcoffset() is None or
                booking.starts_at >= booking.ends_at):
            raise ValueError("invalid existing booking")
        if (booking.starts_at < ends_at + timedelta(minutes=turnover_minutes) and
                starts_at < booking.ends_at + timedelta(minutes=turnover_minutes)):
            ids = [i for i in ids if i != booking.table_id]
    return sorted(ids)
