"""Offline KDS orphan-ticket review; never deletes or voids tickets automatically."""
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class RoutedOrder:
    venue_id: str
    order_id: str
    station: str
    status: str  # accepted or voided


@dataclass(frozen=True)
class TicketReference:
    venue_id: str
    order_id: str
    station: str
    ticket_id: str


def orphan_tickets(orders: Iterable[RoutedOrder], tickets: Iterable[TicketReference],
                   *, authorized_venue_id: str) -> tuple[TicketReference, ...]:
    """Flag tickets lacking an accepted routed order, including voided-order tickets.

    Trusted inputs only; the caller must derive authorized_venue_id from its session.
    Review is manual because historical/voided tickets may be legitimate evidence.
    """
    if not authorized_venue_id:
        raise ValueError('authorized venue required')
    accepted = set()
    seen_orders = set()
    for order in orders:
        if order.venue_id != authorized_venue_id:
            continue
        if not order.order_id or order.station not in ('kitchen', 'bar') or order.status not in ('accepted', 'voided'):
            raise ValueError('invalid routed order')
        key = (order.order_id, order.station)
        if key in seen_orders:
            raise ValueError('duplicate routed order')
        seen_orders.add(key)
        if order.status == 'accepted':
            accepted.add(key)
    seen_tickets = set()
    flagged = []
    for ticket in tickets:
        if ticket.venue_id != authorized_venue_id:
            continue
        if not ticket.order_id or not ticket.ticket_id or ticket.station not in ('kitchen', 'bar'):
            raise ValueError('invalid ticket reference')
        key = (ticket.order_id, ticket.station)
        if key in seen_tickets:
            raise ValueError('duplicate ticket reference')
        seen_tickets.add(key)
        if key not in accepted:
            flagged.append(ticket)
    return tuple(sorted(flagged, key=lambda t: (t.station, t.order_id, t.ticket_id)))
