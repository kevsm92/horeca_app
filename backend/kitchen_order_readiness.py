"""Offline KDS order readiness across kitchen/bar; advisory, not order fulfilment."""
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class OrderStationTicket:
    venue_id: str
    order_id: str
    ticket_id: str
    station: str
    status: str


@dataclass(frozen=True)
class OrderReadiness:
    order_id: str
    ready_for_handoff: bool
    pending_stations: tuple[str, ...]


def order_readiness(tickets: Iterable[OrderStationTicket], *, authorized_venue_id: str,
                    order_id: str, required_stations: tuple[str, ...]) -> OrderReadiness:
    """Fail closed on missing/duplicate stations; never infer service completion."""
    if not authorized_venue_id or not order_id:
        raise ValueError("venue and order required")
    if (not required_stations or len(set(required_stations)) != len(required_stations)
            or any(s not in ("kitchen", "bar") for s in required_stations)):
        raise ValueError("invalid required stations")
    found = {}
    for ticket in tickets:
        if ticket.venue_id != authorized_venue_id or ticket.order_id != order_id:
            continue
        if (not ticket.ticket_id or ticket.station not in ("kitchen", "bar")
                or ticket.status not in ("queued", "preparing", "ready", "served", "cancelled")):
            raise ValueError("invalid ticket")
        if ticket.station not in required_stations:
            raise ValueError("unexpected station ticket")
        if ticket.station in found:
            raise ValueError("duplicate station ticket")
        found[ticket.station] = ticket.status
    pending = tuple(s for s in required_stations if found.get(s) not in ("ready", "served"))
    return OrderReadiness(order_id, not pending, pending)
