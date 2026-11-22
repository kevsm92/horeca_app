"""Offline PO line preview, scoped and reconciled against approved snapshot total."""
import sqlite3


def preview_lines(db: sqlite3.Connection, *, venue_id: str, draft_id: str) -> list[dict] | None:
    """Requires independently authenticated, venue-authorized caller; no network I/O."""
    if not all(isinstance(x, str) and x.strip() for x in (venue_id, draft_id)):
        raise ValueError("venue and draft required")
    header = db.execute("""SELECT requisition_id,total_cents FROM offline_po_drafts
        WHERE venue_id=? AND id=? AND offline_only=1""", (venue_id, draft_id)).fetchone()
    if header is None:
        return None
    rows = db.execute("""SELECT sku,quantity,unit_price_cents FROM purchase_requisition_lines
        WHERE venue_id=? AND requisition_id=? ORDER BY id""", (venue_id, header[0])).fetchall()
    if not rows or any(not sku or type(q) is not int or q <= 0 or
                       type(p) is not int or p < 0 for sku, q, p in rows):
        raise ValueError("missing or invalid lines")
    total = sum(q*p for _, q, p in rows)
    if total > 2**63-1 or total != header[1]:
        raise ValueError("snapshot total mismatch; manual review required")
    return [dict(sku=sku, quantity=q, unit_price_cents=p, line_total_cents=q*p)
            for sku, q, p in rows]


if __name__ == "__main__":
    import unittest

    class Tests(unittest.TestCase):
        def setUp(self):
            self.db = sqlite3.connect(":memory:")
            self.db.executescript("""CREATE TABLE offline_po_drafts(
                id TEXT,venue_id TEXT,requisition_id TEXT,total_cents INTEGER,offline_only INTEGER);
                CREATE TABLE purchase_requisition_lines(
                id TEXT,requisition_id TEXT,venue_id TEXT,sku TEXT,quantity INTEGER,unit_price_cents INTEGER);
                INSERT INTO offline_po_drafts VALUES ('p','a','r',500,1),('other','b','r2',100,1);
                INSERT INTO purchase_requisition_lines VALUES
                ('l1','r','a','milk',2,250),('l2','r','b','secret',1,9999);""")

        def tearDown(self):
            self.db.close()

        def test_scoped_preview(self):
            self.assertEqual(preview_lines(self.db, venue_id="a", draft_id="p"),
                             [dict(sku="milk", quantity=2, unit_price_cents=250,
                                   line_total_cents=500)])
            self.assertIsNone(preview_lines(self.db, venue_id="a", draft_id="other"))

        def test_drift_fails_closed(self):
            self.db.execute("UPDATE purchase_requisition_lines SET quantity=3 WHERE id='l1'")
            with self.assertRaises(ValueError):
                preview_lines(self.db, venue_id="a", draft_id="p")

        def test_bad_scope(self):
            with self.assertRaises(ValueError):
                preview_lines(self.db, venue_id="", draft_id="p")

    unittest.main()
