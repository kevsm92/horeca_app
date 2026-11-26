"""Pure offline KDS station queue projection; never infers tickets from orders."""
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class QueueTicket:
    venue_id: str
    ticket_id: str
    station: str
    status: str
    revision: int


def station_queue(tickets: Iterable[QueueTicket], *, authorized_venue_id: str,
                  station: str) -> tuple[QueueTicket, ...]:
    """Show actionable tickets only; require a trusted server-derived venue."""
    if not authorized_venue_id or station not in ("kitchen", "bar"):
        raise ValueError("invalid venue or station")
    result = []
    seen = set()
    for ticket in tickets:
        if ticket.venue_id != authorized_venue_id or ticket.station != station:
            continue
        if not ticket.ticket_id or ticket.status not in (
                "queued", "preparing", "ready", "served", "cancelled"):
            raise ValueError("invalid ticket")
        if type(ticket.revision) is not int or ticket.revision < 0:
            raise ValueError("invalid revision")
        if ticket.ticket_id in seen:
            raise ValueError("duplicate ticket; reconcile upstream")
        seen.add(ticket.ticket_id)
        if ticket.status in ("queued", "preparing", "ready"):
            result.append(ticket)
    priority = {"ready": 0, "preparing": 1, "queued": 2}
    return tuple(sorted(result, key=lambda t: (priority[t.status], t.ticket_id)))
