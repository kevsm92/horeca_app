"""Offline, synthetic-only Tables occupancy projection (2026-11-12).

A UI read model, not a source of truth or authenticated seating endpoint.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class TableView:
    table_id: str
    physical_seats: int
    status: str
    guests: int


def project_occupancy(inventory, active_sessions):
    """Return ordered immutable rows; reject inconsistent input rather than masking it.

    inventory: iterable of (table_id, physical_seats)
    active_sessions: iterable of (table_id, guests) for active sessions only.
    """
    capacity = {}
    for table_id, seats in inventory:
        if not isinstance(table_id, str) or not table_id or table_id in capacity:
            raise ValueError("invalid or duplicate physical table")
        if type(seats) is not int or seats < 1:
            raise ValueError("invalid physical seat count")
        capacity[table_id] = seats
    occupied = {}
    for table_id, guests in active_sessions:
        if table_id not in capacity:
            raise ValueError("session references unknown physical table")
        if table_id in occupied:
            raise ValueError("multiple active sessions for physical table")
        if type(guests) is not int or not 1 <= guests <= capacity[table_id]:
            raise ValueError("invalid occupied guest count")
        occupied[table_id] = guests
    return tuple(
        TableView(table_id, seats, "occupied" if table_id in occupied else "available",
                  occupied.get(table_id, 0))
        for table_id, seats in capacity.items()
    )
