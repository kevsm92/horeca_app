"""Read-only offline purchase-order draft lines. Caller must enforce authenticated venue RBAC; never sends orders."""
import sqlite3

def list_offline_po_lines(connection: sqlite3.Connection, *, venue_id: str, draft_id: str) -> list[dict]:
    """Reject corrupt or stale requisition projections; return deterministic EUR-cent lines."""
    if not all(isinstance(v, str) and v.strip() for v in (venue_id, draft_id)):
        raise ValueError("venue and draft required")
    draft = connection.execute(
        """SELECT requisition_id, approved_revision, total_cents, offline_only
           FROM offline_po_drafts WHERE id=? AND venue_id=?""", (draft_id, venue_id)
    ).fetchone()
    if draft is None:
        return []
    req_id, revision, expected_total, offline_only = draft
    if offline_only != 1:
        raise ValueError("non-offline draft forbidden")
    req = connection.execute(
        """SELECT revision, status FROM purchase_requisitions
           WHERE id=? AND venue_id=?""", (req_id, venue_id)
    ).fetchone()
    if req is None or req != (revision, "approved"):
        raise ValueError("draft requisition provenance mismatch")
    rows = connection.execute(
        """SELECT sku, quantity, unit_price_cents FROM purchase_requisition_lines
           WHERE requisition_id=? AND venue_id=? ORDER BY sku, id""", (req_id, venue_id)
    ).fetchall()
    if not rows or any(type(q) is not int or q <= 0 or
                       type(p) is not int or p < 0 for _, q, p in rows):
        raise ValueError("invalid draft lines")
    total = sum(q * p for _, q, p in rows)
    if total > 2**63 - 1 or total != expected_total:
        raise ValueError("draft total mismatch")
    return [dict(sku=sku, quantity=q, unit_price_cents=p,
                 line_total_cents=q * p, currency="EUR") for sku, q, p in rows]
