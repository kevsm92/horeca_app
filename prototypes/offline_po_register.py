"""Offline-only PO draft register. No supplier transmission or HTTP API.
Run: cd prototypes && python -m unittest offline_po_register -v
"""
from dataclasses import dataclass
import unittest
from purchasing import Requisition, Status

@dataclass(frozen=True)
class PurchaseOrderDraft:
    id: str
    venue_id: str
    requisition_id: str
    supplier_id: str
    sku: str
    quantity: int
    unit_price_cents: int
    approved_by: str
    state: str = "OFFLINE_DRAFT_NOT_SENT"

    @property
    def total_cents(self):
        return self.quantity * self.unit_price_cents

class OfflinePORegister:
    """In-memory prototype. Production needs transactional unique constraints.
    Venue and role must be derived from authenticated server context.
    """
    def __init__(self):
        self._by_requisition = {}
        self._ids = set()

    def create_from_approved(self, req: Requisition, *, venue_id: str,
                             actor_role: str, po_id: str) -> PurchaseOrderDraft:
        if req.venue_id != venue_id or actor_role != "purchasing_manager":
            raise PermissionError("unauthorized venue or role")
        if req.status is not Status.APPROVED or not req.reviewer_id:
            raise ValueError("independent approval required")
        if not isinstance(po_id, str) or not po_id.strip():
            raise ValueError("nonempty PO ID required")
        key = (venue_id, req.id)
        if key in self._by_requisition:
            existing = self._by_requisition[key]
            if existing.id != po_id:
                raise ValueError("requisition already has a PO draft")
            return existing
        if po_id in self._ids:
            raise ValueError("duplicate PO ID")
        po = PurchaseOrderDraft(po_id, venue_id, req.id, req.supplier_id,
                                req.sku, req.quantity, req.unit_price_cents,
                                req.reviewer_id)
        self._by_requisition[key] = po
        self._ids.add(po_id)
        return po

class OfflinePORegisterTests(unittest.TestCase):
    def setUp(self):
        self.register = OfflinePORegister()
        self.req = Requisition("r1", "fictional-a", "fictional-staff",
                               "fictional-vendor", "DEMO-SKU", 3, 125,
                               Status.APPROVED, "fictional-manager")

    def test_draft_and_idempotent_retry(self):
        args = dict(venue_id="fictional-a", actor_role="purchasing_manager", po_id="po1")
        po = self.register.create_from_approved(self.req, **args)
        self.assertEqual((po.total_cents, po.state), (375, "OFFLINE_DRAFT_NOT_SENT"))
        self.assertIs(po, self.register.create_from_approved(self.req, **args))
        with self.assertRaises(ValueError):
            self.register.create_from_approved(self.req, **{**args, "po_id": "po2"})

    def test_venue_and_role_denied(self):
        for venue, role in [("fictional-b", "purchasing_manager"), ("fictional-a", "staff")]:
            with self.assertRaises(PermissionError):
                self.register.create_from_approved(self.req, venue_id=venue,
                                                   actor_role=role, po_id="po1")

    def test_unapproved_denied(self):
        for status, reviewer in [(Status.SUBMITTED, None), (Status.APPROVED, None)]:
            req = Requisition("r1", "fictional-a", "fictional-staff", "fictional-vendor",
                              "DEMO-SKU", 3, 125, status, reviewer)
            with self.assertRaises(ValueError):
                self.register.create_from_approved(req, venue_id="fictional-a",
                                                   actor_role="purchasing_manager", po_id="po1")

    def test_po_id_collision(self):
        self.register.create_from_approved(self.req, venue_id="fictional-a",
                                           actor_role="purchasing_manager", po_id="po1")
        other = Requisition("r2", "fictional-a", "fictional-staff", "fictional-vendor",
                            "DEMO-SKU", 1, 200, Status.APPROVED, "fictional-manager")
        with self.assertRaises(ValueError):
            self.register.create_from_approved(other, venue_id="fictional-a",
                                               actor_role="purchasing_manager", po_id="po1")

if __name__ == "__main__":
    unittest.main()
