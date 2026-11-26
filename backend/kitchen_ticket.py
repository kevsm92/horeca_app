"""Offline venue-scoped KDS ticket state transitions (synthetic only)."""
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Literal

Status = Literal["queued", "preparing", "ready", "served", "cancelled"]
ALLOWED = {
    "queued": frozenset({"preparing", "cancelled"}),
    "preparing": frozenset({"ready", "cancelled"}),
    "ready": frozenset({"served"}),
    "served": frozenset(),
    "cancelled": frozenset(),
}


@dataclass(frozen=True)
class Ticket:
    venue_id: str
    ticket_id: str
    station: Literal["kitchen", "bar"]
    status: Status = "queued"
    revision: int = 0
    updated_at: str = ""


def transition(ticket: Ticket, *, actor_venue_id: str, expected_revision: int,
               new_status: Status, at: datetime) -> Ticket:
    """Pure compare-and-swap transition; persistence must enforce CAS atomically."""
    if not ticket.venue_id or not ticket.ticket_id or ticket.station not in ("kitchen", "bar"):
        raise ValueError("invalid ticket identity or station")
    if actor_venue_id != ticket.venue_id:
        raise PermissionError("venue mismatch")
    if type(expected_revision) is not int or expected_revision != ticket.revision:
        raise ValueError("stale ticket revision")
    if new_status not in ALLOWED[ticket.status]:
        raise ValueError("invalid ticket transition")
    if at.tzinfo is None or at.utcoffset() is None:
        raise ValueError("timezone-aware event timestamp required")
    return replace(ticket, status=new_status, revision=ticket.revision + 1,
                   updated_at=at.astimezone(timezone.utc).isoformat())
