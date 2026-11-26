"""Synthetic KDS station workload snapshot, not employee productivity tracking."""
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class StationLine:
    venue_id: str
    ticket_id: str
    station: str
    status: str
    item_id: str
    quantity: int


def station_load(lines: Iterable[StationLine], *, authorized_venue_id: str,
                 station: str) -> dict[str, int]:
    """Aggregate active item quantities by status, without staff identifiers.

    Caller supplies a server-derived venue and enforces station authorization.
    Input is one line per (ticket, item); duplicate lines fail closed.
    """
    if not authorized_venue_id or station not in ("kitchen", "bar"):
        raise ValueError("invalid venue or station")
    totals = {"queued": 0, "preparing": 0, "ready": 0}
    seen = set()
    for line in lines:
        if line.venue_id != authorized_venue_id or line.station != station:
            continue
        if (not line.ticket_id or not line.item_id or
                line.status not in (*totals, "served", "cancelled") or
                type(line.quantity) is not int or line.quantity <= 0):
            raise ValueError("invalid station line")
        key = (line.ticket_id, line.item_id)
        if key in seen:
            raise ValueError("duplicate station line")
        seen.add(key)
        if line.status in totals:
            totals[line.status] += line.quantity
    return totals
