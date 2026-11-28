import unittest
from kitchen_ticket_intake import IntakeRoute, IntakeTicket, plan_intake


class IntakeTests(unittest.TestCase):
    def setUp(self):
        self.route = IntakeRoute("venue-a", "order-1", "kitchen", "accepted")

    def test_new_and_retry(self):
        ticket, created = plan_intake(self.route, (), authorized_venue_id="venue-a")
        self.assertTrue(created)
        self.assertEqual(ticket.status, "queued")
        self.assertEqual(plan_intake(self.route, (ticket,), authorized_venue_id="venue-a"), (ticket, False))

    def test_station_independence(self):
        kitchen, _ = plan_intake(self.route, (), authorized_venue_id="venue-a")
        bar, created = plan_intake(IntakeRoute("venue-a", "order-1", "bar", "accepted"), (kitchen,), authorized_venue_id="venue-a")
        self.assertTrue(created)
        self.assertNotEqual(kitchen.ticket_id, bar.ticket_id)

    def test_cross_venue_denied(self):
        with self.assertRaises(PermissionError):
            plan_intake(self.route, (), authorized_venue_id="venue-b")

    def test_voided_and_invalid_rejected(self):
        for status in ("voided", "pending"):
            with self.subTest(status=status), self.assertRaises(ValueError):
                plan_intake(IntakeRoute("venue-a", "order-1", "kitchen", status), (), authorized_venue_id="venue-a")

    def test_duplicate_and_corrupt_fail_closed(self):
        ticket, _ = plan_intake(self.route, (), authorized_venue_id="venue-a")
        with self.assertRaises(ValueError):
            plan_intake(self.route, (ticket, ticket), authorized_venue_id="venue-a")
        with self.assertRaises(ValueError):
            plan_intake(self.route, (IntakeTicket("venue-a", "order-1", "kitchen", "", "queued"),), authorized_venue_id="venue-a")

    def test_other_venue_ticket_not_reused(self):
        foreign = IntakeTicket("venue-b", "order-1", "kitchen", "foreign")
        _, created = plan_intake(self.route, (foreign,), authorized_venue_id="venue-a")
        self.assertTrue(created)


if __name__ == "__main__":
    unittest.main()
