"""Pure offline validation for table dimensions and configured seats."""
from dataclasses import dataclass


@dataclass(frozen=True)
class TableInventory:
    venue_id: str
    table_id: str
    physical_seats: int
    configured_seats: int
    active_guests: int
    width_cm: int
    depth_cm: int
    revision: int


def resize_table(table: TableInventory, *, venue_id: str, expected_revision: int,
                 width_cm: int, depth_cm: int, seats: int) -> TableInventory:
    """Return a revised value; persistence must enforce compare-and-swap atomically."""
    if not table.venue_id or not table.table_id or venue_id != table.venue_id:
        raise ValueError("venue mismatch")
    if expected_revision != table.revision:
        raise ValueError("stale revision")
    if table.physical_seats < 1 or not 0 <= table.configured_seats <= table.physical_seats or table.active_guests < 0 or table.active_guests > table.physical_seats:
        raise ValueError("invalid physical inventory or occupancy")
    if not isinstance(width_cm, int) or isinstance(width_cm, bool) or not 40 <= width_cm <= 400:
        raise ValueError("invalid width")
    if not isinstance(depth_cm, int) or isinstance(depth_cm, bool) or not 40 <= depth_cm <= 400:
        raise ValueError("invalid depth")
    if not isinstance(seats, int) or isinstance(seats, bool) or not table.active_guests <= seats <= table.physical_seats:
        raise ValueError("seats exceed inventory or fall below occupancy")
    return TableInventory(table.venue_id, table.table_id, table.physical_seats, seats,
                          table.active_guests, width_cm, depth_cm, table.revision + 1)
