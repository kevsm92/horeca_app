"""Offline KDS missing-ticket reconciliation; reports gaps, never creates tickets."""
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class RoutedOrder:
    venue_id: str
    order_id: str
    station: str
    status: str  # accepted, voided


@dataclass(frozen=True)
class TicketReference:
    venue_id: str
    order_id: str
    station: str
    ticket_id: str


def missing_tickets(orders: Iterable[RoutedOrder], tickets: Iterable[TicketReference],
                    *, authorized_venue_id: str) -> tuple[tuple[str, str], ...]:
    """Return missing (order_id, station) pairs for accepted synthetic orders.

    Both inputs must be read from trusted storage; venue scope is server-derived.
    Duplicate source keys fail closed instead of masking inconsistent routing.
    """
    if not authorized_venue_id:
        raise ValueError('authorized venue required')
    expected = set()
    for order in orders:
        if order.venue_id != authorized_venue_id:
            continue
        if not order.order_id or order.station not in ('kitchen', 'bar') or order.status not in ('accepted', 'voided'):
            raise ValueError('invalid routed order')
        key = (order.order_id, order.station)
        if key in expected:
            raise ValueError('duplicate routed order')
        expected.add(key)
        if order.status == 'voided':
            expected.remove(key)
    present = set()
    for ticket in tickets:
        if ticket.venue_id != authorized_venue_id:
            continue
        if not ticket.order_id or not ticket.ticket_id or ticket.station not in ('kitchen', 'bar'):
            raise ValueError('invalid ticket reference')
        key = (ticket.order_id, ticket.station)
        if key in present:
            raise ValueError('duplicate ticket reference')
        present.add(key)
    return tuple(sorted(expected - present))
