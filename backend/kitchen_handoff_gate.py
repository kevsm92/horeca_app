"""Offline KDS order handoff gate: each required station needs a matching pickup ack."""
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class StationHandoff:
    venue_id: str
    order_id: str
    ticket_id: str
    station: str
    status: str
    revision: int


@dataclass(frozen=True)
class StationAck:
    venue_id: str
    ticket_id: str
    ticket_revision: int
    actor_id: str


def handoff_gate(tickets: Iterable[StationHandoff], acknowledgements: Iterable[StationAck],
                 *, authorized_venue_id: str, order_id: str,
                 required_stations: tuple[str, ...]) -> tuple[str, ...]:
    """Return stations awaiting handoff; never infer physical delivery.

    The caller authenticates staff, authorizes roles and atomically stores acks.
    Foreign-venue records are ignored, not treated as valid evidence.
    """
    if not authorized_venue_id or not order_id:
        raise ValueError("venue and order required")
    if (not required_stations or len(set(required_stations)) != len(required_stations)
            or any(s not in ("kitchen", "bar") for s in required_stations)):
        raise ValueError("invalid required stations")
    found = {}
    for t in tickets:
        if t.venue_id != authorized_venue_id or t.order_id != order_id:
            continue
        if (not t.ticket_id or t.station not in required_stations
                or t.status not in ("queued", "preparing", "ready", "served", "cancelled")
                or type(t.revision) is not int or t.revision < 0):
            raise ValueError("invalid station ticket")
        if t.station in found:
            raise ValueError("duplicate station ticket")
        found[t.station] = t
    acks = {}
    for a in acknowledgements:
        if a.venue_id != authorized_venue_id:
            continue
        if not a.ticket_id or not a.actor_id.strip() or type(a.ticket_revision) is not int or a.ticket_revision < 0:
            raise ValueError("invalid acknowledgement")
        key = (a.ticket_id, a.ticket_revision)
        if key in acks:
            raise ValueError("duplicate acknowledgement")
        acks[key] = a
    return tuple(s for s in required_stations if s not in found
                 or found[s].status != "ready"
                 or (found[s].ticket_id, found[s].revision) not in acks)
