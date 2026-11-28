"""Offline KDS pickup handoff: explicit acknowledgement, never inferred from ready status."""
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class Pickup:
    venue_id: str
    ticket_id: str
    station: str
    status: str
    revision: int


@dataclass(frozen=True)
class PickupAcknowledgement:
    venue_id: str
    ticket_id: str
    ticket_revision: int
    actor_id: str
    acknowledged_at: str


def acknowledge_pickup(ticket: Pickup, *, authorized_venue_id: str, actor_id: str,
                       expected_revision: int, at: datetime) -> PickupAcknowledgement:
    """Record a human handoff for a ready ticket; caller must persist with atomic CAS.

    Authentication and station/role authorization are prerequisites at the API boundary.
    This pure function does not change ticket status or establish physical delivery.
    """
    if not authorized_venue_id or ticket.venue_id != authorized_venue_id:
        raise PermissionError("venue mismatch")
    if not ticket.ticket_id or ticket.station not in ("kitchen", "bar") or not actor_id.strip():
        raise ValueError("invalid ticket or actor")
    if type(ticket.revision) is not int or ticket.revision < 0:
        raise ValueError("invalid revision")
    if type(expected_revision) is not int or expected_revision != ticket.revision:
        raise ValueError("stale ticket revision")
    if ticket.status != "ready":
        raise ValueError("only ready tickets may be acknowledged")
    if not isinstance(at, datetime) or at.tzinfo is None or at.utcoffset() is None:
        raise ValueError("timezone-aware acknowledgement required")
    return PickupAcknowledgement(ticket.venue_id, ticket.ticket_id, ticket.revision,
                                 actor_id, at.astimezone(timezone.utc).isoformat())
