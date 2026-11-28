"""Offline SOP applicability gate; a match is not inspection evidence."""
from dataclasses import dataclass


@dataclass(frozen=True)
class SOPScope:
    venue_id: str
    revision: int
    roles: frozenset[str]
    stations: frozenset[str]
    equipment_ids: frozenset[str]


def applicable(scope: SOPScope, *, venue_id: str, role: str, station: str,
               equipment_id: str | None = None) -> bool:
    """All populated dimensions must match; empty sets mean venue-wide."""
    if not scope.venue_id or scope.revision < 1:
        raise ValueError('invalid published SOP scope')
    if not venue_id or not role or not station:
        raise ValueError('missing trusted assignment context')
    if venue_id != scope.venue_id:
        return False
    return (not scope.roles or role in scope.roles) and (not scope.stations or station in scope.stations) and (not scope.equipment_ids or equipment_id in scope.equipment_ids)
