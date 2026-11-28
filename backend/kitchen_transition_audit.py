"""Offline KDS transition audit verification; never changes ticket state."""
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from kitchen_ticket import Ticket, transition


@dataclass(frozen=True)
class TransitionEvent:
    venue_id: str
    ticket_id: str
    from_status: str
    to_status: str
    expected_revision: int
    at: datetime


def replay_transitions(initial: Ticket, events: Iterable[TransitionEvent], *,
                       authorized_venue_id: str) -> Ticket:
    """Fail closed on missing, reordered, foreign or forged transition events."""
    if not authorized_venue_id or initial.venue_id != authorized_venue_id:
        raise PermissionError('venue mismatch')
    current = initial
    for event in events:
        if event.venue_id != authorized_venue_id or event.ticket_id != current.ticket_id:
            raise PermissionError('event identity mismatch')
        if event.from_status != current.status:
            raise ValueError('transition origin mismatch')
        current = transition(current, actor_venue_id=authorized_venue_id,
                             expected_revision=event.expected_revision,
                             new_status=event.to_status, at=event.at)
    return current
