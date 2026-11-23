"""Offline receipt identity gate for synthetic invoice matching; no posting."""
from dataclasses import dataclass
from receiving_invoice_batch import reconcile_invoice_batch


@dataclass(frozen=True)
class ReceiptReference:
    venue_id: str
    purchase_order_id: str
    receipt_id: str
    status: str


def reconcile_for_receipt(*, venue_id, po_venue_id, invoice_venue_id,
                          purchase_order_id, receipt, accepted_receipt_lines,
                          invoice_lines):
    """Require an accepted receipt bound to the exact PO before comparing lines.

    This does not fetch persisted receipts; callers must supply trusted records.
    """
    if not isinstance(receipt, ReceiptReference):
        raise ValueError("trusted receipt reference required")
    if not all(isinstance(v, str) and v.strip() for v in (
            receipt.venue_id, receipt.purchase_order_id, receipt.receipt_id)):
        raise ValueError("receipt identity missing")
    if receipt.venue_id != venue_id:
        raise PermissionError("cross-venue receipt denied")
    if receipt.purchase_order_id != purchase_order_id:
        raise ValueError("receipt belongs to a different purchase order")
    if receipt.status != "accepted":
        raise ValueError("receipt must be accepted before invoice matching")
    return reconcile_invoice_batch(
        venue_id=venue_id, po_venue_id=po_venue_id,
        receipt_venue_id=receipt.venue_id, invoice_venue_id=invoice_venue_id,
        purchase_order_id=purchase_order_id,
        accepted_receipt_lines=accepted_receipt_lines,
        invoice_lines=invoice_lines,
    )
