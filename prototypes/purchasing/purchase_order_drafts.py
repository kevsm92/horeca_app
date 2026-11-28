"""Offline synthetic purchase-order approval prototype. No network or supplier I/O."""
from dataclasses import dataclass, replace
from typing import Tuple
import unittest

@dataclass(frozen=True)
class DraftLine:
    sku: str
    quantity: int
    unit_price_cents: int

    def __post_init__(self):
        if not self.sku.strip() or self.quantity <= 0 or self.unit_price_cents < 0:
            raise ValueError("Invalid SKU, quantity, or unit price")

@dataclass(frozen=True)
class PurchaseOrderDraft:
    draft_id: str
    venue_id: str
    supplier_id: str
    lines: Tuple[DraftLine, ...]
    status: str = "draft"
    approved_by: str | None = None

    def __post_init__(self):
        if not all((self.draft_id.strip(), self.venue_id.strip(), self.supplier_id.strip())):
            raise ValueError("Draft, venue and supplier IDs are required")
        if not self.lines or not isinstance(self.lines, tuple):
            raise ValueError("A draft requires an immutable nonempty line tuple")
        if self.status not in ("draft", "approved"):
            raise ValueError("Unknown status")
        if (self.status == "approved") != (self.approved_by is not None):
            raise ValueError("Approval provenance required exactly when approved")

    @property
    def total_cents(self) -> int:
        return sum(line.quantity * line.unit_price_cents for line in self.lines)

def approve_draft(draft: PurchaseOrderDraft, *, actor_id: str, actor_venue_id: str,
                  actor_role: str, approval_limit_cents: int) -> PurchaseOrderDraft:
    """Return approved snapshot; persistence and audit remain caller responsibilities."""
    if not actor_id.strip() or actor_venue_id != draft.venue_id:
        raise PermissionError("Actor not authorized for venue")
    if actor_role not in ("manager", "owner"):
        raise PermissionError("Approval role required")
    if draft.status != "draft":
        raise ValueError("Draft already finalized")
    if approval_limit_cents < 0 or draft.total_cents > approval_limit_cents:
        raise PermissionError("Approval limit exceeded")
    return replace(draft, status="approved", approved_by=actor_id)

class PurchaseOrderDraftTests(unittest.TestCase):
    def setUp(self):
        self.draft = PurchaseOrderDraft("PO-SYN-1", "VENUE-A", "SUP-SYN-1",
                                        (DraftLine("FLOUR-SYN", 3, 1250),))
        self.args = dict(actor_id="MGR-SYN", actor_venue_id="VENUE-A",
                         actor_role="manager", approval_limit_cents=5000)

    def test_integer_cent_total(self):
        self.assertEqual(self.draft.total_cents, 3750)

    def test_approval_preserves_original_draft(self):
        approved = approve_draft(self.draft, **self.args)
        self.assertEqual((approved.status, approved.approved_by), ("approved", "MGR-SYN"))
        self.assertEqual(self.draft.status, "draft")

    def test_cross_venue_denied(self):
        with self.assertRaises(PermissionError):
            approve_draft(self.draft, **(self.args | {"actor_venue_id": "VENUE-B"}))

    def test_non_manager_denied(self):
        with self.assertRaises(PermissionError):
            approve_draft(self.draft, **(self.args | {"actor_role": "staff"}))

    def test_over_limit_denied(self):
        with self.assertRaises(PermissionError):
            approve_draft(self.draft, **(self.args | {"approval_limit_cents": 3749}))

    def test_repeat_approval_denied(self):
        with self.assertRaises(ValueError):
            approve_draft(approve_draft(self.draft, **self.args), **self.args)

    def test_invalid_lines_denied(self):
        for qty, price in ((0, 10), (1, -1)):
            with self.assertRaises(ValueError):
                DraftLine("SKU", qty, price)

    def test_no_lines_denied(self):
        with self.assertRaises(ValueError):
            PurchaseOrderDraft("X", "A", "S", ())

if __name__ == "__main__":
    unittest.main()
