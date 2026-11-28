"""Offline KDS review queue for voided orders with still-active station tickets.

Advisory only: never auto-cancel preparation or issue refunds.
"""
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class VoidOrder:
    venue_id: str
    order_id: str
    status: str  # accepted | voided


@dataclass(frozen=True)
class StationTicket:
    venue_id: str
    order_id: str
    ticket_id: str
    station: str
    status: str  # queued | preparing | ready | served | cancelled


def void_review_queue(orders: Iterable[VoidOrder], tickets: Iterable[StationTicket],
                      *, authorized_venue_id: str) -> tuple[StationTicket, ...]:
    """Flag active tickets for voided orders, rejecting ambiguous trusted inputs."""
    if not authorized_venue_id:
        raise ValueError("authorized venue required")
    statuses = {}
    for order in orders:
        if order.venue_id != authorized_venue_id:
            continue
        if not order.order_id or order.status not in ("accepted", "voided"):
            raise ValueError("invalid order")
        if order.order_id in statuses:
            raise ValueError("duplicate order")
        statuses[order.order_id] = order.status
    seen = set()
    review = []
    for ticket in tickets:
        if ticket.venue_id != authorized_venue_id:
            continue
        if (not ticket.order_id or not ticket.ticket_id or
                ticket.station not in ("kitchen", "bar") or
                ticket.status not in ("queued", "preparing", "ready", "served", "cancelled")):
            raise ValueError("invalid ticket")
        key = (ticket.order_id, ticket.station)
        if key in seen:
            raise ValueError("duplicate station ticket")
        seen.add(key)
        if ticket.order_id not in statuses:
            raise ValueError("orphan ticket: reconcile upstream")
        if statuses[ticket.order_id] == "voided" and ticket.status in ("queued", "preparing", "ready"):
            review.append(ticket)
    return tuple(sorted(review, key=lambda t: (t.order_id, t.station, t.ticket_id)))
