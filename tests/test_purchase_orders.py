import unittest
from dataclasses import dataclass
from horeca.purchase_orders import draft_from_approved

@dataclass
class Req:
    id: str = "r1"
    venue_id: str = "v1"
    supplier_id: str = "fictional"
    sku: str = "SKU"
    quantity: int = 4
    unit_price_cents: int = 250
    status: str = "approved"
    approver_id: str = "approver"

class PurchaseOrderDraftTests(unittest.TestCase):
    def test_approved_draft_is_local(self):
        draft = draft_from_approved(Req(), venue_id="v1", actor_id="manager",
                                    role="manager", draft_id="po1")
        self.assertEqual((draft.total_cents, draft.status, draft.approved_by),
                         (1000, "draft", "approver"))

    def test_reject_unapproved(self):
        with self.assertRaises(ValueError):
            draft_from_approved(Req(status="submitted"), venue_id="v1",
                                actor_id="manager", role="manager", draft_id="po1")

    def test_reject_cross_venue_and_staff(self):
        for venue, role in (("v2", "manager"), ("v1", "staff")):
            with self.subTest(venue=venue, role=role), self.assertRaises(PermissionError):
                draft_from_approved(Req(), venue_id=venue, actor_id="manager",
                                    role=role, draft_id="po1")

    def test_reject_blank_identifier(self):
        with self.assertRaises(ValueError):
            draft_from_approved(Req(), venue_id="v1", actor_id="manager",
                                role="manager", draft_id=" ")
