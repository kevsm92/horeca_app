"""Pure, fail-closed preflight for seating requests; DB remains final authority."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Assignment:
    venue_id: str
    table_id: str
    guest_count: int


def validate_assignment(request: Assignment, inventory: dict, active_sessions: dict) -> None:
    """Raise ValueError on invalid assignment; keys are (venue_id, table_id).

    This preflight does not replace transactional database constraints.
    """
    if not isinstance(request.venue_id, str) or not request.venue_id.strip():
        raise ValueError('venue required')
    if not isinstance(request.table_id, str) or not request.table_id.strip():
        raise ValueError('physical table required')
    if type(request.guest_count) is not int or request.guest_count <= 0:
        raise ValueError('positive integer guest count required')
    key = (request.venue_id, request.table_id)
    if key not in inventory:
        raise ValueError('table not in venue inventory')
    capacity = inventory[key]
    if type(capacity) is not int or capacity <= 0:
        raise ValueError('invalid physical capacity')
    if request.guest_count > capacity:
        raise ValueError('capacity exceeded')
    if key in active_sessions:
        raise ValueError('table already occupied')
