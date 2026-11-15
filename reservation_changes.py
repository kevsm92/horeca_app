"""Offline reservation amendment/cancellation policy. Caller must enforce atomic DB CAS."""
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from reservation_availability import Table, Occupancy, available_tables


@dataclass(frozen=True)
class Reservation:
    venue_id: str
    reservation_id: str
    table_id: str
    starts_at: datetime
    ends_at: datetime
    status: str
    revision: int
    party_size: int


def amend_reservation(*, booking: Reservation, expected_revision: int,
                      venue_id: str, new_table_id: str, new_start: datetime,
                      duration: timedelta, turnover: timedelta,
                      tables: tuple[Table, ...],
                      reservations: tuple[Reservation, ...]) -> Reservation:
    """Pure proposal only; repeat validation under venue-scoped write lock."""
    if not venue_id or booking.venue_id != venue_id:
        raise ValueError('venue mismatch')
    if type(expected_revision) is not int or expected_revision < 0 or booking.revision != expected_revision:
        raise ValueError('stale revision')
    if booking.status != 'confirmed':
        raise ValueError('only confirmed bookings can be amended')
    if not new_table_id or not booking.reservation_id:
        raise ValueError('identifiers required')
    seen = set()
    occupancies = []
    for other in reservations:
        if other.venue_id != venue_id:
            continue
        if not other.reservation_id or other.reservation_id in seen:
            raise ValueError('duplicate reservation identifier')
        seen.add(other.reservation_id)
        if other.reservation_id == booking.reservation_id:
            if other != booking:
                raise ValueError('authoritative booking differs')
            continue
        occupancies.append(Occupancy(other.venue_id, other.table_id,
                                     other.starts_at, other.ends_at, other.status))
    if booking.reservation_id not in seen:
        raise ValueError('booking missing from authoritative set')
    if new_table_id not in available_tables(venue_id, booking.party_size, new_start,
                                            duration, turnover, tables, tuple(occupancies)):
        raise ValueError('table unavailable')
    return replace(booking, table_id=new_table_id, starts_at=new_start,
                   ends_at=new_start + duration, revision=booking.revision + 1)


def cancel_reservation(*, booking: Reservation, expected_revision: int,
                       venue_id: str) -> Reservation:
    if not venue_id or booking.venue_id != venue_id:
        raise ValueError('venue mismatch')
    if type(expected_revision) is not int or expected_revision < 0 or booking.revision != expected_revision:
        raise ValueError('stale revision')
    if booking.status != 'confirmed':
        raise ValueError('only confirmed bookings can be cancelled')
    return replace(booking, status='cancelled', revision=booking.revision + 1)
