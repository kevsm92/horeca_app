"""Offline KDS station summary from trusted venue-scoped ticket projections."""
from dataclasses import dataclass
from typing import Iterable

from kitchen_queue import QueueTicket, station_queue


@dataclass(frozen=True)
class StationSummary:
    station: str
    queued: int
    preparing: int
    ready: int
    actionable: int


def summarize_station(tickets: Iterable[QueueTicket], *, authorized_venue_id: str,
                      station: str) -> StationSummary:
    """Count actionable tickets, excluding served/cancelled and other venues.

    Duplicate and corrupt in-scope tickets fail closed via station_queue.
    This is an internal synthetic projection, not evidence of staff performance.
    """
    queue = station_queue(tickets, authorized_venue_id=authorized_venue_id, station=station)
    counts = {status: sum(ticket.status == status for ticket in queue)
              for status in ("queued", "preparing", "ready")}
    return StationSummary(station, counts["queued"], counts["preparing"],
                          counts["ready"], len(queue))
