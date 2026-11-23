"""Read-only SQLite receipt lookup for offline invoice matching (synthetic fixtures)."""
import sqlite3
from receiving_invoice_batch import InvoiceLine
from receiving_invoice_identity import ReceiptReference, reconcile_for_receipt


def reconcile_stored_receipt(conn: sqlite3.Connection, *, venue_id: str,
                             purchase_order_id: str, receipt_id: str,
                             invoice_venue_id: str, invoice_lines):
    """Never accept caller-supplied receipt status or accepted quantities."""
    if not all(isinstance(x, str) and x.strip() for x in
               (venue_id, purchase_order_id, receipt_id, invoice_venue_id)):
        raise ValueError("nonempty receipt and venue identities required")
    if invoice_venue_id != venue_id:
        raise PermissionError("cross-venue invoice denied")
    row = conn.execute(
        "SELECT venue_id, purchase_order_id, status FROM receiving_receipts "
        "WHERE venue_id = ? AND receipt_id = ?", (venue_id, receipt_id)
    ).fetchone()
    if row is None:
        raise ValueError("accepted receipt not found in venue")
    receipt = ReceiptReference(row[0], row[1], receipt_id, row[2])
    if receipt.purchase_order_id != purchase_order_id or receipt.status != "accepted":
        raise ValueError("receipt not accepted for requested purchase order")
    po = conn.execute(
        "SELECT venue_id FROM receiving_purchase_orders WHERE venue_id = ? AND purchase_order_id = ?",
        (venue_id, purchase_order_id)
    ).fetchone()
    if po is None:
        raise ValueError("purchase order not found in venue")
    rows = conn.execute(
        "SELECT sku, accepted_units, agreed_unit_cents FROM receiving_receipt_lines "
        "WHERE venue_id = ? AND receipt_id = ? ORDER BY sku", (venue_id, receipt_id)
    ).fetchall()
    if not rows:
        raise ValueError("accepted receipt has no lines")
    return reconcile_for_receipt(
        venue_id=venue_id, po_venue_id=po[0], invoice_venue_id=invoice_venue_id,
        purchase_order_id=purchase_order_id, receipt=receipt,
        accepted_receipt_lines=[InvoiceLine(*line) for line in rows],
        invoice_lines=invoice_lines,
    )
