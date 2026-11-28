"""Offline KDS ticket transitions; synthetic data only. Run: python -m unittest kds_ticket -v."""
from dataclasses import dataclass, replace
from enum import Enum
import unittest

class State(str, Enum):
    QUEUED = "queued"
    PREPARING = "preparing"
    READY = "ready"
    SERVED = "served"
    CANCELLED = "cancelled"

ALLOWED = {
    State.QUEUED: {State.PREPARING, State.CANCELLED},
    State.PREPARING: {State.READY, State.CANCELLED},
    State.READY: {State.SERVED},
    State.SERVED: set(),
    State.CANCELLED: set(),
}

@dataclass(frozen=True)
class Ticket:
    ticket_id: str
    venue_id: str
    station: str
    state: State = State.QUEUED
    revision: int = 0

    def __post_init__(self):
        if not self.ticket_id or not self.venue_id or self.station not in {"kitchen", "bar"}:
            raise ValueError("ticket requires ID, venue and kitchen/bar station")
        if self.revision < 0:
            raise ValueError("negative revision")

def transition(ticket: Ticket, *, venue_id: str, expected_revision: int, new_state: State) -> Ticket:
    """Tenant-bound optimistic transition; caller must authenticate and authorize upstream."""
    if venue_id != ticket.venue_id:
        raise PermissionError("venue mismatch")
    if expected_revision != ticket.revision:
        raise ValueError("stale ticket revision")
    if not isinstance(new_state, State) or new_state not in ALLOWED[ticket.state]:
        raise ValueError("illegal ticket transition")
    return replace(ticket, state=new_state, revision=ticket.revision + 1)

class TicketTests(unittest.TestCase):
    def setUp(self):
        self.ticket = Ticket("fictional-1", "fictional-venue-a", "kitchen")

    def test_happy_path(self):
        t = self.ticket
        for state in (State.PREPARING, State.READY, State.SERVED):
            t = transition(t, venue_id=t.venue_id, expected_revision=t.revision, new_state=state)
        self.assertEqual((t.state, t.revision), (State.SERVED, 3))

    def test_tenant_isolation(self):
        with self.assertRaises(PermissionError):
            transition(self.ticket, venue_id="fictional-venue-b", expected_revision=0, new_state=State.PREPARING)

    def test_stale_revision(self):
        with self.assertRaises(ValueError):
            transition(self.ticket, venue_id=self.ticket.venue_id, expected_revision=1, new_state=State.PREPARING)

    def test_cannot_skip_or_reopen(self):
        with self.assertRaises(ValueError):
            transition(self.ticket, venue_id=self.ticket.venue_id, expected_revision=0, new_state=State.SERVED)
        cancelled = transition(self.ticket, venue_id=self.ticket.venue_id, expected_revision=0, new_state=State.CANCELLED)
        with self.assertRaises(ValueError):
            transition(cancelled, venue_id=cancelled.venue_id, expected_revision=1, new_state=State.PREPARING)

    def test_station_validation(self):
        with self.assertRaises(ValueError):
            Ticket("x", "v", "unknown")

    def test_invalid_state_rejected(self):
        with self.assertRaises(ValueError):
            transition(self.ticket, venue_id=self.ticket.venue_id, expected_revision=0, new_state="preparing")

if __name__ == "__main__":
    unittest.main()
