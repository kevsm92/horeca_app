"""Manager-authorized offline roster read boundary; not an HTTP endpoint.

Callers must obtain the principal from a verified server session, never from
request-supplied role/venue fields. No attendance is inferred from schedules.
"""
from dataclasses import dataclass
from datetime import date
from prototypes.weekly_roster import week_snapshot


@dataclass(frozen=True)
class Principal:
    staff_id: str
    venue_id: str
    role: str
    authenticated: bool


def manager_week_snapshot(db, *, principal: Principal, monday: date):
    if not isinstance(principal, Principal) or not principal.authenticated:
        raise PermissionError("authentication required")
    if not principal.staff_id or not principal.venue_id or principal.role not in ("manager", "owner"):
        raise PermissionError("manager role required")
    return week_snapshot(db, venue_id=principal.venue_id, monday=monday)
