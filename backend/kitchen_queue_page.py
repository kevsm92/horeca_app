"""Bounded, stable offline KDS queue paging over trusted station projection.

Cursor is an exclusive (status priority, ticket ID) key. Clients must restart
paging after a queue mutation; this pure read model does not snapshot storage.
"""
from dataclasses import dataclass
from typing import Iterable

from kitchen_queue import QueueTicket, station_queue

_PRIORITY = {"ready": 0, "preparing": 1, "queued": 2}


@dataclass(frozen=True)
class QueuePage:
    tickets: tuple[QueueTicket, ...]
    next_cursor: tuple[int, str] | None


def page_station_queue(tickets: Iterable[QueueTicket], *, authorized_venue_id: str,
                       station: str, limit: int = 25,
                       after: tuple[int, str] | None = None) -> QueuePage:
    """Return one bounded page; venue scope must come from a trusted session.

    Invalid cursors and limits fail closed. This is an offline projection only.
    """
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError("limit must be an integer between 1 and 100")
    if after is not None:
        if (type(after) is not tuple or len(after) != 2
                or type(after[0]) is not int or after[0] not in _PRIORITY.values()
                or type(after[1]) is not str or not after[1]):
            raise ValueError("invalid queue cursor")
    queue = station_queue(tickets, authorized_venue_id=authorized_venue_id,
                          station=station)
    remaining = tuple(ticket for ticket in queue
                      if after is None or (_PRIORITY[ticket.status], ticket.ticket_id) > after)
    page = remaining[:limit]
    cursor = (_PRIORITY[page[-1].status], page[-1].ticket_id) if len(remaining) > limit else None
    return QueuePage(page, cursor)
