"""Offline-only venue-scoped purchase requisition domain; no supplier transmission."""
from dataclasses import dataclass, replace
from enum import Enum

class Status(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"

@dataclass(frozen=True)
class Requisition:
    id: str
    venue_id: str
    requester_id: str
    supplier_id: str
    sku: str
    quantity: int
    unit_price_cents: int
    status: Status = Status.DRAFT
    reviewer_id: str | None = None

    def __post_init__(self):
        if not all((self.id, self.venue_id, self.requester_id, self.supplier_id, self.sku)):
            raise ValueError("identifiers must be nonempty")
        if type(self.quantity) is not int or self.quantity <= 0:
            raise ValueError("quantity must be positive integer")
        if type(self.unit_price_cents) is not int or not 0 <= self.unit_price_cents <= 10**9:
            raise ValueError("unit price must be nonnegative integer cents")
        if self.quantity * self.unit_price_cents > 10**12:
            raise ValueError("requisition exceeds mock amount limit")

    @property
    def total_cents(self):
        return self.quantity * self.unit_price_cents

def transition(req: Requisition, *, venue_id: str, actor_id: str, actor_role: str, action: str) -> Requisition:
    """Caller must persist under a transaction/revision lock."""
    if req.venue_id != venue_id:
        raise PermissionError("venue mismatch")
    if action == "submit" and req.status is Status.DRAFT and actor_id == req.requester_id:
        return replace(req, status=Status.SUBMITTED)
    if action in ("approve", "reject") and req.status is Status.SUBMITTED:
        if actor_role != "purchasing_manager" or actor_id == req.requester_id:
            raise PermissionError("independent purchasing manager required")
        return replace(req, status=Status.APPROVED if action == "approve" else Status.REJECTED, reviewer_id=actor_id)
    raise ValueError("invalid transition")

def offline_po_preview(req: Requisition, *, venue_id: str, actor_role: str) -> dict:
    if req.venue_id != venue_id or actor_role != "purchasing_manager":
        raise PermissionError("unauthorized preview")
    if req.status is not Status.APPROVED:
        raise ValueError("approval required")
    return {"kind": "OFFLINE_DRAFT_NOT_SENT", "requisition_id": req.id,
            "venue_id": req.venue_id, "supplier_id": req.supplier_id,
            "sku": req.sku, "quantity": req.quantity, "total_cents": req.total_cents,
            "currency": "EUR"}
