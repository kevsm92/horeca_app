"""Offline deterministic routing of accepted synthetic order lines to KDS stations.

Caller must derive venue from an authenticated session and persist tickets
atomically; no writes, dispatch or external communication occur here.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class OrderLine:
    line_id: str
    item_id: str
    quantity: int
    station: str


@dataclass(frozen=True)
class StationBatch:
    venue_id: str
    order_id: str
    station: str
    lines: tuple[OrderLine, ...]


def route_order(*, authorized_venue_id: str, order_venue_id: str,
                order_id: str, order_status: str,
                lines: tuple[OrderLine, ...]) -> tuple[StationBatch, ...]:
    """Fail closed on malformed input; return kitchen then bar batches."""
    if not authorized_venue_id or authorized_venue_id != order_venue_id:
        raise PermissionError("venue mismatch")
    if not order_id or order_status != "accepted" or not lines:
        raise ValueError("accepted nonempty order required")
    seen = set()
    buckets = {"kitchen": [], "bar": []}
    for line in lines:
        if (not isinstance(line, OrderLine) or not line.line_id or
                not line.item_id or line.line_id in seen or
                type(line.quantity) is not int or line.quantity <= 0 or
                line.station not in buckets):
            raise ValueError("invalid or duplicate order line")
        seen.add(line.line_id)
        buckets[line.station].append(line)
    return tuple(StationBatch(order_venue_id, order_id, station, tuple(buckets[station]))
                 for station in ("kitchen", "bar") if buckets[station])
