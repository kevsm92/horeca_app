"""Offline venue-scoped floor-plan coordinate contract (synthetic-only prototype)."""
from dataclasses import dataclass, replace

class LayoutConflict(ValueError):
    """Editor must refresh a stale revision."""

@dataclass(frozen=True)
class TablePosition:
    venue_id: str
    table_id: str
    x: int
    y: int
    revision: int = 0

def move_table(position: TablePosition, *, venue_id: str, table_id: str,
               expected_revision: int, x: int, y: int,
               canvas_width: int, canvas_height: int) -> TablePosition:
    """Pure validation; persistence MUST use an atomic revision compare-and-swap."""
    if not venue_id or not table_id or position.venue_id != venue_id or position.table_id != table_id:
        raise ValueError("table does not belong to requested venue")
    if type(expected_revision) is not int or expected_revision != position.revision:
        raise LayoutConflict("stale floor-plan revision")
    if any(type(v) is not int for v in (x, y, canvas_width, canvas_height)):
        raise ValueError("coordinates and canvas dimensions must be integers")
    if canvas_width <= 0 or canvas_height <= 0 or not (0 <= x < canvas_width and 0 <= y < canvas_height):
        raise ValueError("position outside canvas")
    if (x, y) == (position.x, position.y):
        return position
    return replace(position, x=x, y=y, revision=position.revision + 1)

def keyboard_move(position: TablePosition, *, key: str, step: int = 10,
                  canvas_width: int, canvas_height: int) -> TablePosition:
    """Arrow keys move a selected table; clamp to canvas bounds."""
    if type(step) is not int or step <= 0:
        raise ValueError("step must be a positive integer")
    delta = {"ArrowLeft": (-step, 0), "ArrowRight": (step, 0),
             "ArrowUp": (0, -step), "ArrowDown": (0, step)}.get(key)
    if delta is None:
        raise ValueError("unsupported keyboard key")
    if canvas_width <= 0 or canvas_height <= 0:
        raise ValueError("invalid canvas")
    return move_table(position, venue_id=position.venue_id, table_id=position.table_id,
                      expected_revision=position.revision,
                      x=max(0, min(canvas_width - 1, position.x + delta[0])),
                      y=max(0, min(canvas_height - 1, position.y + delta[1])),
                      canvas_width=canvas_width, canvas_height=canvas_height)
