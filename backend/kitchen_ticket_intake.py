"""Pure offline KDS intake planner for trusted accepted synthetic order routes.

Caller must atomically persist with unique (venue_id, order_id, station).
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class IntakeRoute:
    venue_id: str
    order_id: str
    station: str
    order_status: str


@dataclass(frozen=True)
class IntakeTicket:
    venue_id: str
    order_id: str
    station: str
    ticket_id: str
    status: str = "queued"


def plan_intake(route: IntakeRoute, existing: tuple[IntakeTicket, ...], *,
                authorized_venue_id: str) -> tuple[IntakeTicket, bool]:
    """Plan idempotent intake; never mutate storage or trigger side effects."""
    if not authorized_venue_id or route.venue_id != authorized_venue_id:
        raise PermissionError("venue mismatch")
    if not route.order_id or route.station not in ("kitchen", "bar"):
        raise ValueError("invalid route")
    if route.order_status != "accepted":
        raise ValueError("only accepted orders can enter KDS")
    matches = []
    for ticket in existing:
        if ticket.venue_id != authorized_venue_id:
            continue
        if (ticket.order_id, ticket.station) == (route.order_id, route.station):
            matches.append(ticket)
    if len(matches) > 1:
        raise ValueError("duplicate persisted ticket references")
    if matches:
        ticket = matches[0]
        if not ticket.ticket_id or ticket.status not in ("queued", "preparing", "ready", "served", "cancelled"):
            raise ValueError("corrupt persisted ticket")
        return ticket, False
    key = f"{len(route.order_id)}:{route.order_id}:{route.station}"
    return IntakeTicket(route.venue_id, route.order_id, route.station, key), True
