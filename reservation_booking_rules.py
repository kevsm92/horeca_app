"""Offline venue-configured booking-window gate; no guest data or network effects."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(frozen=True)
class BookingRules:
    min_party: int
    max_party: int
    min_lead: timedelta
    max_advance: timedelta
    min_duration: timedelta
    max_duration: timedelta


def validate_booking_window(*, party: int, start: datetime, duration: timedelta,
                            now: datetime, rules: BookingRules) -> None:
    """Fail closed on malformed policy, UTC instants, and booking boundaries."""
    if any(type(v) is not int for v in (party, rules.min_party, rules.max_party)):
        raise ValueError('party sizes must be integers')
    if not (1 <= rules.min_party <= rules.max_party and rules.min_party <= party <= rules.max_party):
        raise ValueError('party size outside configured limits')
    for dt in (start, now):
        if not isinstance(dt, datetime) or dt.tzinfo is None or dt.utcoffset() is None:
            raise ValueError('aware timestamps required')
    for td in (duration, rules.min_lead, rules.max_advance, rules.min_duration, rules.max_duration):
        if not isinstance(td, timedelta):
            raise ValueError('durations must be timedelta')
    if not (timedelta(0) <= rules.min_lead <= rules.max_advance and
            timedelta(0) < rules.min_duration <= rules.max_duration):
        raise ValueError('invalid venue booking policy')
    if not rules.min_duration <= duration <= rules.max_duration:
        raise ValueError('duration outside configured limits')
    lead = start.astimezone(timezone.utc) - now.astimezone(timezone.utc)
    if not rules.min_lead <= lead <= rules.max_advance:
        raise ValueError('booking outside lead/advance window')
