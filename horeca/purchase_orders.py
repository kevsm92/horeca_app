"""Local-only purchase-order drafts from approved requisitions."""
from dataclasses import dataclass

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
    status: str = "draft"

    @property
    def total_cents(self):
        return self.quantity * self.unit_price_cents

def draft_from_approved(req, *, venue_id, actor_id, role, draft_id):
    """Pure offline transformation; persistence must uniquely index venue/requisition."""
    if not venue_id or venue_id != req.venue_id:
        raise PermissionError("wrong venue")
    if role not in ("manager", "owner") or not actor_id:
        raise PermissionError("manager authorization required")
    if req.status != "approved" or not req.approver_id:
        raise ValueError("approved requisition required")
    if not isinstance(draft_id, str) or not draft_id.strip():
        raise ValueError("draft id required")
    return PurchaseOrderDraft(draft_id, req.venue_id, req.id, req.supplier_id,
                              req.sku, req.quantity, req.unit_price_cents,
                              req.approver_id)
