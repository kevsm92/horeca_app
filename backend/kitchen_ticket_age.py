"""Offline KDS age flags for venue-scoped actionable tickets; not staff scoring."""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable


@dataclass(frozen=True)
class TimedTicket:
    venue_id: str
    ticket_id: str
    station: str
    status: str
    accepted_at: datetime


@dataclass(frozen=True)
class AgeFlag:
    ticket_id: str
    station: str
    age_minutes: int
    overdue: bool


def ticket_age_flags(tickets: Iterable[TimedTicket], *, authorized_venue_id: str,
                     station: str, now: datetime, threshold_minutes: int) -> tuple[AgeFlag, ...]:
    """Project queue age using an explicitly configured threshold, never auto-escalate."""
    if not authorized_venue_id or station not in ('kitchen', 'bar'):
        raise ValueError('invalid venue or station')
    if type(threshold_minutes) is not int or not 1 <= threshold_minutes <= 1440:
        raise ValueError('invalid configured threshold')
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise ValueError('aware now required')
    seen = set()
    flags = []
    for ticket in tickets:
        if ticket.venue_id != authorized_venue_id or ticket.station != station:
            continue
        if (not ticket.ticket_id or ticket.status not in
                ('queued', 'preparing', 'ready', 'served', 'cancelled')):
            raise ValueError('invalid ticket')
        if ticket.ticket_id in seen:
            raise ValueError('duplicate ticket')
        seen.add(ticket.ticket_id)
        if (not isinstance(ticket.accepted_at, datetime) or ticket.accepted_at.tzinfo is None
                or ticket.accepted_at.utcoffset() is None):
            raise ValueError('aware accepted_at required')
        seconds = (now.astimezone(timezone.utc) - ticket.accepted_at.astimezone(timezone.utc)).total_seconds()
        if seconds < 0:
            raise ValueError('future accepted_at')
        if ticket.status in ('queued', 'preparing', 'ready'):
            minutes = int(seconds // 60)
            flags.append(AgeFlag(ticket.ticket_id, station, minutes,
                                 seconds >= threshold_minutes * 60))
    return tuple(sorted(flags, key=lambda item: (-item.age_minutes, item.ticket_id)))
