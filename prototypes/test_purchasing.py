import unittest
from purchasing import Requisition, Status, transition, offline_po_preview

class PurchasingTests(unittest.TestCase):
    def setUp(self):
        self.req = Requisition("req-1", "venue-a", "worker-1", "vendor-fake", "SKU-X", 3, 125)

    def test_approval_and_offline_preview(self):
        submitted = transition(self.req, venue_id="venue-a", actor_id="worker-1", actor_role="staff", action="submit")
        approved = transition(submitted, venue_id="venue-a", actor_id="manager-2", actor_role="purchasing_manager", action="approve")
        self.assertEqual(approved.total_cents, 375)
        self.assertEqual(offline_po_preview(approved, venue_id="venue-a", actor_role="purchasing_manager")["kind"], "OFFLINE_DRAFT_NOT_SENT")
        self.assertEqual(self.req.status, Status.DRAFT)

    def test_tenant_isolation(self):
        with self.assertRaises(PermissionError):
            transition(self.req, venue_id="venue-b", actor_id="worker-1", actor_role="staff", action="submit")
        with self.assertRaises(PermissionError):
            offline_po_preview(self.req, venue_id="venue-b", actor_role="purchasing_manager")

    def test_separation_of_duties(self):
        submitted = transition(self.req, venue_id="venue-a", actor_id="worker-1", actor_role="staff", action="submit")
        for role, actor in [("purchasing_manager", "worker-1"), ("staff", "manager-2")]:
            with self.assertRaises(PermissionError):
                transition(submitted, venue_id="venue-a", actor_id=actor, actor_role=role, action="approve")

    def test_reject_and_invalid_transitions(self):
        with self.assertRaises(ValueError):
            transition(self.req, venue_id="venue-a", actor_id="manager-2", actor_role="purchasing_manager", action="approve")
        submitted = transition(self.req, venue_id="venue-a", actor_id="worker-1", actor_role="staff", action="submit")
        rejected = transition(submitted, venue_id="venue-a", actor_id="manager-2", actor_role="purchasing_manager", action="reject")
        with self.assertRaises(ValueError):
            offline_po_preview(rejected, venue_id="venue-a", actor_role="purchasing_manager")

    def test_invalid_money_quantity(self):
        for qty, price in [(0, 10), (1, -1), (True, 10), (2, 0.5), (100000, 10**9)]:
            with self.assertRaises(ValueError):
                Requisition("r", "v", "u", "s", "sku", qty, price)

    def test_cancel_unapproved_only(self):
        cancelled = transition(self.req, venue_id="venue-a", actor_id="worker-1", actor_role="staff", action="cancel")
        self.assertEqual(cancelled.status, Status.CANCELLED)
        submitted = transition(self.req, venue_id="venue-a", actor_id="worker-1", actor_role="staff", action="submit")
        manager_cancelled = transition(submitted, venue_id="venue-a", actor_id="manager-2", actor_role="purchasing_manager", action="cancel")
        self.assertEqual(manager_cancelled.status, Status.CANCELLED)
        with self.assertRaises(PermissionError):
            transition(submitted, venue_id="venue-b", actor_id="manager-2", actor_role="purchasing_manager", action="cancel")
        with self.assertRaises(PermissionError):
            transition(submitted, venue_id="venue-a", actor_id="other", actor_role="staff", action="cancel")
        approved = transition(submitted, venue_id="venue-a", actor_id="manager-2", actor_role="purchasing_manager", action="approve")
        with self.assertRaises(ValueError):
            transition(approved, venue_id="venue-a", actor_id="worker-1", actor_role="staff", action="cancel")
        with self.assertRaises(ValueError):
            transition(cancelled, venue_id="venue-a", actor_id="worker-1", actor_role="staff", action="submit")

if __name__ == "__main__":
    unittest.main()
