"""Focused synthetic-data checks for offline purchasing domain."""
import unittest
from dataclasses import replace
from purchasing.purchase_drafts import Requisition, Status, review, make_draft


class PurchasingTests(unittest.TestCase):
    def setUp(self):
        self.req = Requisition("r1", "venue-a", "fictional-supplier", "SKU-1", 3, 125, "staff-1")

    def test_approved_offline_draft(self):
        approved = review(self.req, actor_id="manager-1", actor_venue_id="venue-a",
                          actor_role="manager", approve=True, approval_limit_cents=500)
        draft = make_draft(approved, venue_id="venue-a")
        self.assertEqual((draft.total_cents, draft.status), (375, "offline_draft_not_sent"))

    def test_tenant_isolation(self):
        with self.assertRaises(PermissionError):
            review(self.req, actor_id="m", actor_venue_id="venue-b", actor_role="manager",
                   approve=True, approval_limit_cents=1000)
        with self.assertRaises(PermissionError):
            make_draft(replace(self.req, status=Status.APPROVED), venue_id="venue-b")

    def test_self_approval_and_role(self):
        for actor, role in (("staff-1", "manager"), ("m", "staff")):
            with self.assertRaises(PermissionError):
                review(self.req, actor_id=actor, actor_venue_id="venue-a",
                       actor_role=role, approve=True, approval_limit_cents=1000)

    def test_limit_and_rejection(self):
        with self.assertRaises(PermissionError):
            review(self.req, actor_id="m", actor_venue_id="venue-a", actor_role="owner",
                   approve=True, approval_limit_cents=374)
        rejected = review(self.req, actor_id="m", actor_venue_id="venue-a",
                          actor_role="owner", approve=False, approval_limit_cents=0)
        with self.assertRaises(ValueError):
            make_draft(rejected, venue_id="venue-a")
        with self.assertRaises(ValueError):
            review(rejected, actor_id="m2", actor_venue_id="venue-a", actor_role="owner",
                   approve=True, approval_limit_cents=1000)

    def test_integer_invariants(self):
        for changes in ({"quantity": 0}, {"quantity": True},
                        {"unit_price_cents": -1}, {"unit_price_cents": 1.5}):
            with self.assertRaises(ValueError):
                replace(self.req, **changes)


if __name__ == "__main__":
    unittest.main()
