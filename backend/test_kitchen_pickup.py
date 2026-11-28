import unittest
from datetime import datetime, timezone
from kitchen_pickup import Pickup, acknowledge_pickup

NOW = datetime(2026, 11, 26, 14, 0, tzinfo=timezone.utc)


class PickupTests(unittest.TestCase):
    def setUp(self):
        self.ticket = Pickup("fictional-a", "ticket-1", "bar", "ready", 2)

    def ack(self, ticket=None, **overrides):
        args = dict(authorized_venue_id="fictional-a", actor_id="fictional-staff-1",
                    expected_revision=2, at=NOW)
        args.update(overrides)
        return acknowledge_pickup(ticket or self.ticket, **args)

    def test_ready_handoff_records_provenance_without_mutating_ticket(self):
        result = self.ack()
        self.assertEqual((result.ticket_id, result.ticket_revision, result.actor_id),
                         ("ticket-1", 2, "fictional-staff-1"))
        self.assertEqual(result.acknowledged_at, "2026-11-26T14:00:00+00:00")
        self.assertEqual(self.ticket.status, "ready")

    def test_other_venue_rejected(self):
        with self.assertRaises(PermissionError):
            self.ack(authorized_venue_id="fictional-b")

    def test_non_ready_rejected(self):
        with self.assertRaises(ValueError):
            self.ack(Pickup("fictional-a", "ticket-1", "bar", "preparing", 2))

    def test_stale_revision_rejected(self):
        with self.assertRaises(ValueError):
            self.ack(expected_revision=1)

    def test_missing_actor_rejected(self):
        with self.assertRaises(ValueError):
            self.ack(actor_id="  ")

    def test_naive_timestamp_rejected(self):
        with self.assertRaises(ValueError):
            self.ack(at=datetime(2026, 11, 26))

    def test_invalid_revision_type_rejected(self):
        with self.assertRaises(ValueError):
            self.ack(expected_revision=True)


if __name__ == "__main__":
    unittest.main()
