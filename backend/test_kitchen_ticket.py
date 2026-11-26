import unittest
from datetime import datetime, timezone
from kitchen_ticket import Ticket, transition

NOW = datetime(2026, 11, 26, 1, 0, tzinfo=timezone.utc)


class TicketTests(unittest.TestCase):
    def test_valid_path(self):
        ticket = Ticket("venue-a", "ticket-1", "kitchen")
        for revision, state in enumerate(("preparing", "ready", "served")):
            ticket = transition(ticket, actor_venue_id="venue-a", expected_revision=revision,
                                new_status=state, at=NOW)
        self.assertEqual((ticket.status, ticket.revision), ("served", 3))

    def test_cross_venue_denied(self):
        with self.assertRaises(PermissionError):
            transition(Ticket("venue-a", "1", "bar"), actor_venue_id="venue-b",
                       expected_revision=0, new_status="preparing", at=NOW)

    def test_stale_revision_denied(self):
        with self.assertRaisesRegex(ValueError, "stale"):
            transition(Ticket("venue-a", "1", "bar"), actor_venue_id="venue-a",
                       expected_revision=1, new_status="preparing", at=NOW)

    def test_illegal_skip_denied(self):
        with self.assertRaisesRegex(ValueError, "invalid ticket transition"):
            transition(Ticket("venue-a", "1", "bar"), actor_venue_id="venue-a",
                       expected_revision=0, new_status="served", at=NOW)

    def test_terminal_cannot_reopen(self):
        with self.assertRaises(ValueError):
            transition(Ticket("venue-a", "1", "bar", "cancelled"), actor_venue_id="venue-a",
                       expected_revision=0, new_status="preparing", at=NOW)

    def test_naive_time_denied(self):
        with self.assertRaises(ValueError):
            transition(Ticket("venue-a", "1", "bar"), actor_venue_id="venue-a",
                       expected_revision=0, new_status="preparing", at=datetime(2026, 11, 26))


if __name__ == "__main__":
    unittest.main()
