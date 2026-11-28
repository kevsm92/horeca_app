"""Offline reference availability logic. Advisory only; never commit a booking without transactional recheck."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

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

def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timezone-aware timestamps required")
    return value.astimezone(timezone.utc)

def available_tables(venue_id: str, guests: int, starts_at: datetime,
                     duration: timedelta, turnover: timedelta,
                     tables: list[Table], bookings: list[Booking]) -> list[str]:
    """Check capacity, venue isolation and half-open intervals with turnover buffers."""
    start = _utc(starts_at)
    if not venue_id or guests < 1 or duration <= timedelta(0) or turnover < timedelta(0):
        raise ValueError("invalid reservation parameters")
    end = start + duration
    eligible = []
    for table in tables:
        if table.venue_id != venue_id or table.seats < guests or table.seats < 1:
            continue
        if any(b.venue_id == venue_id and b.table_id == table.table_id
               and b.status in {"confirmed", "seated"}
               and start < _utc(b.ends_at) + turnover
               and _utc(b.starts_at) < end + turnover
               for b in bookings):
            continue
        eligible.append(table.table_id)
    return sorted(set(eligible))
