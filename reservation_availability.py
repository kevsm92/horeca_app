"""Pure, fail-closed table-aware reservation availability policy.

Intervals are timezone-aware instants, half-open [start, end).
No persistence, authentication, booking creation or guest communication here.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(frozen=True)
class Table:
    venue_id: str
    table_id: str
    capacity: int


@dataclass(frozen=True)
class Occupancy:
    venue_id: str
    table_id: str
    starts_at: datetime
    ends_at: datetime
    status: str  # confirmed, seated, cancelled


def available_tables(venue_id: str, party_size: int, starts_at: datetime,
                     duration: timedelta, turnover: timedelta,
                     tables: tuple[Table, ...],
                     occupancies: tuple[Occupancy, ...]) -> tuple[str, ...]:
    """Return tables without conflicting blocked windows.

    Turnover applies after each occupancy and after the proposed reservation.
    A DB write transaction must repeat this check and enforce no overlaps.
    """
    if not isinstance(venue_id, str) or not venue_id.strip():
        raise ValueError('venue required')
    if type(party_size) is not int or party_size < 1:
        raise ValueError('positive integer party size required')
    if not isinstance(starts_at, datetime) or starts_at.tzinfo is None or starts_at.utcoffset() is None:
        raise ValueError('timezone-aware start required')
    if not isinstance(duration, timedelta) or duration <= timedelta(0):
        raise ValueError('positive duration required')
    if not isinstance(turnover, timedelta) or turnover < timedelta(0):
        raise ValueError('nonnegative turnover required')
    start = starts_at.astimezone(timezone.utc)
    end = start + duration + turnover
    seen = set()
    candidates = []
    for table in tables:
        if table.venue_id != venue_id:
            continue
        if not table.table_id or table.table_id in seen or type(table.capacity) is not int or table.capacity < 1:
            raise ValueError('invalid or duplicate table inventory')
        seen.add(table.table_id)
        if table.capacity >= party_size:
            candidates.append(table.table_id)
    blocked = set()
    for booking in occupancies:
        if booking.venue_id != venue_id:
            continue
        if booking.table_id not in seen:
            raise ValueError('booking references unknown table')
        if booking.status not in ('confirmed', 'seated', 'cancelled'):
            raise ValueError('unknown booking status')
        if booking.status == 'cancelled':
            continue
        a, b = booking.starts_at, booking.ends_at
        if any(not isinstance(t, datetime) or t.tzinfo is None or t.utcoffset() is None for t in (a, b)):
            raise ValueError('timezone-aware booking bounds required')
        a, b = a.astimezone(timezone.utc), b.astimezone(timezone.utc)
        if b <= a:
            raise ValueError('invalid booking interval')
        if start < b + turnover and a < end:
            blocked.add(booking.table_id)
    return tuple(t for t in candidates if t not in blocked)
