"""Offline roster revision validation; no persistence or attendance inference."""
from datetime import datetime, timezone
from dataclasses import dataclass

class RosterConflict(ValueError):
    pass

@dataclass(frozen=True)
class Shift:
    staff_id: str
    starts_at: datetime
    ends_at: datetime
    station_id: str

def validate_roster(shifts: tuple[Shift, ...]) -> None:
    by_staff: dict[str, list[Shift]] = {}
    for shift in shifts:
        if not shift.staff_id or not shift.station_id:
            raise ValueError('staff and station are required')
        if (shift.starts_at.tzinfo is None or shift.starts_at.utcoffset() is None
                or shift.ends_at.tzinfo is None or shift.ends_at.utcoffset() is None):
            raise ValueError('timezone-aware timestamps required')
        if shift.starts_at >= shift.ends_at:
            raise ValueError('shift must end after it starts')
        by_staff.setdefault(shift.staff_id, []).append(shift)
    for group in by_staff.values():
        ordered = sorted(group, key=lambda s: s.starts_at.astimezone(timezone.utc))
        for previous, current in zip(ordered, ordered[1:]):
            if previous.ends_at > current.starts_at:
                raise RosterConflict('overlapping shifts for one staff member')

def propose_revision(*, current_revision: int, expected_revision: int,
                     current_venue: str, requested_venue: str,
                     shifts: tuple[Shift, ...]) -> int:
    """Validate a proposal; persistence must atomically compare-and-swap."""
    if not current_venue or current_venue != requested_venue:
        raise PermissionError('venue mismatch')
    if current_revision < 0 or expected_revision != current_revision:
        raise RosterConflict('stale roster revision')
    validate_roster(shifts)
    return current_revision + 1
