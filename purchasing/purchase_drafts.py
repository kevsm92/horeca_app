"""Offline-only venue-scoped requisition approval and purchase-order draft model.

No supplier dispatch, payment or external integration.
"""
from dataclasses import dataclass, replace
from enum import Enum


class Status(str, Enum):
    REQUESTED = "requested"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass(frozen=True)
class Requisition:
    id: str
    venue_id: str
    supplier_id: str
    sku: str
    quantity: int
    unit_price_cents: int
    requester_id: str
    status: Status = Status.REQUESTED
    reviewer_id: str | None = None

    def __post_init__(self):
        if not all((self.id, self.venue_id, self.supplier_id, self.sku, self.requester_id)):
            raise ValueError("identifiers required")
        if type(self.quantity) is not int or self.quantity <= 0:
            raise ValueError("positive integer quantity required")
        if type(self.unit_price_cents) is not int or self.unit_price_cents < 0:
            raise ValueError("nonnegative integer cents required")

    @property
    def total_cents(self):
        return self.quantity * self.unit_price_cents


@dataclass(frozen=True)
class PurchaseOrderDraft:
    requisition_id: str
    venue_id: str
    supplier_id: str
    sku: str
    quantity: int
    total_cents: int
    status: str = "offline_draft_not_sent"


def review(req: Requisition, *, actor_id: str, actor_venue_id: str,
           actor_role: str, approve: bool, approval_limit_cents: int) -> Requisition:
    if actor_venue_id != req.venue_id:
        raise PermissionError("venue mismatch")
    if actor_role not in ("manager", "owner"):
        raise PermissionError("manager approval required")
    if not actor_id or actor_id == req.requester_id:
        raise PermissionError("self approval forbidden")
    if req.status != Status.REQUESTED:
        raise ValueError("already reviewed")
    if approve and (approval_limit_cents < 0 or req.total_cents > approval_limit_cents):
        raise PermissionError("approval limit exceeded")
    return replace(req, status=Status.APPROVED if approve else Status.REJECTED,
                   reviewer_id=actor_id)


def make_draft(req: Requisition, *, venue_id: str) -> PurchaseOrderDraft:
    if req.venue_id != venue_id:
        raise PermissionError("venue mismatch")
    if req.status != Status.APPROVED:
        raise ValueError("approval required")
    return PurchaseOrderDraft(req.id, req.venue_id, req.supplier_id,
                              req.sku, req.quantity, req.total_cents)
