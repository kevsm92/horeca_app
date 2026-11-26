"""Offline KDS manual expedite ordering; advisory only, no ticket mutations."""
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class ExpediteTicket:
    venue_id: str
    ticket_id: str
    station: str
    status: str
    priority: str  # normal | expedite; manager-confirmed upstream
    revision: int


def expedite_queue(tickets: Iterable[ExpediteTicket], *, authorized_venue_id: str,
                   station: str) -> tuple[ExpediteTicket, ...]:
    """Display explicit expedited tickets first; reject ambiguous input."""
    if not authorized_venue_id or station not in ("kitchen", "bar"):
        raise ValueError("invalid venue or station")
    seen = set()
    result = []
    for ticket in tickets:
        if ticket.venue_id != authorized_venue_id or ticket.station != station:
            continue
        if (not ticket.ticket_id or ticket.status not in
                ("queued", "preparing", "ready", "served", "cancelled") or
                ticket.priority not in ("normal", "expedite") or
                type(ticket.revision) is not int or ticket.revision < 0):
            raise ValueError("invalid ticket")
        if ticket.ticket_id in seen:
            raise ValueError("duplicate ticket")
        seen.add(ticket.ticket_id)
        if ticket.status in ("queued", "preparing", "ready"):
            result.append(ticket)
    return tuple(sorted(result, key=lambda t: (
        t.priority != "expedite", {"ready": 0, "preparing": 1, "queued": 2}[t.status],
        t.ticket_id)))
