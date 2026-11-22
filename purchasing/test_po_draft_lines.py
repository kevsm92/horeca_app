"""Synthetic offline PO line projection tests; run python -m unittest purchasing.test_po_draft_lines."""
import sqlite3
import unittest
from purchasing.po_draft_lines import list_offline_po_lines

class DraftLineTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.executescript("""
            CREATE TABLE offline_po_drafts (id TEXT, venue_id TEXT, requisition_id TEXT,
                approved_revision INTEGER, total_cents INTEGER, offline_only INTEGER);
            CREATE TABLE purchase_requisitions (id TEXT, venue_id TEXT, revision INTEGER, status TEXT);
            CREATE TABLE purchase_requisition_lines (id TEXT, requisition_id TEXT,
                venue_id TEXT, sku TEXT, quantity INTEGER, unit_price_cents INTEGER);
            INSERT INTO purchase_requisitions VALUES ('r1','a',3,'approved');
            INSERT INTO offline_po_drafts VALUES ('d1','a','r1',3,850,1);
            INSERT INTO purchase_requisition_lines VALUES
                ('l1','r1','a','FLOUR',2,125),('l2','r1','a','MILK',3,200);
        """)
    def tearDown(self):
        self.db.close()
    def test_projection_read_only(self):
        before = self.db.total_changes
        self.assertEqual(list_offline_po_lines(self.db, venue_id="a", draft_id="d1"), [
            dict(sku="FLOUR", quantity=2, unit_price_cents=125, line_total_cents=250, currency="EUR"),
            dict(sku="MILK", quantity=3, unit_price_cents=200, line_total_cents=600, currency="EUR")])
        self.assertEqual(self.db.total_changes, before)
    def test_tenant_isolation(self):
        self.assertEqual(list_offline_po_lines(self.db, venue_id="b", draft_id="d1"), [])
        self.assertEqual(list_offline_po_lines(self.db, venue_id="a", draft_id="missing"), [])
        with self.assertRaises(ValueError):
            list_offline_po_lines(self.db, venue_id="", draft_id="d1")
    def test_stale_approval_fails_closed(self):
        self.db.execute("UPDATE purchase_requisitions SET revision=4 WHERE id='r1'")
        with self.assertRaises(ValueError):
            list_offline_po_lines(self.db, venue_id="a", draft_id="d1")
    def test_tampered_total_fails_closed(self):
        self.db.execute("UPDATE offline_po_drafts SET total_cents=849 WHERE id='d1'")
        with self.assertRaises(ValueError):
            list_offline_po_lines(self.db, venue_id="a", draft_id="d1")
    def test_nonoffline_fails_closed(self):
        self.db.execute("UPDATE offline_po_drafts SET offline_only=0 WHERE id='d1'")
        with self.assertRaises(ValueError):
            list_offline_po_lines(self.db, venue_id="a", draft_id="d1")

if __name__ == "__main__":
    unittest.main()
