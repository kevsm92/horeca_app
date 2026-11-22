"""Offline, venue-scoped purchase requisition approval prototype (synthetic only)."""
from dataclasses import dataclass, replace
from enum import Enum


class Status(str, Enum):
    DRAFT = 'draft'
    SUBMITTED = 'submitted'
    APPROVED = 'approved'
    REJECTED = 'rejected'


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
    approver_id: str | None = None

    def __post_init__(self):
        if not all((self.id, self.venue_id, self.requester_id, self.supplier_id, self.sku)):
            raise ValueError('identifiers required')
        if type(self.quantity) is not int or self.quantity <= 0:
            raise ValueError('positive integer quantity required')
        if type(self.unit_price_cents) is not int or self.unit_price_cents < 0:
            raise ValueError('nonnegative integer cents required')
        if self.quantity * self.unit_price_cents > 2**63 - 1:
            raise ValueError('amount exceeds supported range')

    @property
    def total_cents(self):
        return self.quantity * self.unit_price_cents


def transition(req: Requisition, *, venue_id: str, actor_id: str,
               role: str, action: str) -> Requisition:
    """Pure state transition; caller must persist atomically with audit trail.

    No supplier order, notification or payment can be generated here.
    """
    if venue_id != req.venue_id:
        raise PermissionError('wrong venue')
    if action == 'submit' and req.status == Status.DRAFT and actor_id == req.requester_id:
        return replace(req, status=Status.SUBMITTED)
    if action in ('approve', 'reject') and req.status == Status.SUBMITTED:
        if role not in ('manager', 'owner') or actor_id == req.requester_id:
            raise PermissionError('independent manager approval required')
        return replace(req, status=Status.APPROVED if action == 'approve' else Status.REJECTED,
                       approver_id=actor_id)
    raise ValueError('invalid requisition transition')
