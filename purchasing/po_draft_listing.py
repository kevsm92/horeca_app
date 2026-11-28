"""Venue-scoped offline purchase-order draft listing (no outbound I/O)."""
import sqlite3


def list_offline_drafts(connection: sqlite3.Connection, *, venue_id: str) -> list[tuple]:
    """Return (id, requisition_id, revision, supplier_id, total_cents).

    Venue must be derived from an authenticated authorization context by caller.
    No supplier submission or external side effects are possible here.
    """
    if not isinstance(venue_id, str) or not venue_id.strip():
        raise ValueError("venue required")
    return connection.execute(
        """SELECT id, requisition_id, approved_revision, supplier_id, total_cents
           FROM offline_po_drafts WHERE venue_id=?
           ORDER BY requisition_id, approved_revision, id""",
        (venue_id,),
    ).fetchall()


if __name__ == "__main__":
    import unittest

    class OfflineDraftListingTests(unittest.TestCase):
        def setUp(self):
            self.db = sqlite3.connect(":memory:")
            self.db.executescript("""
                CREATE TABLE offline_po_drafts (
                    id TEXT PRIMARY KEY, venue_id TEXT NOT NULL,
                    requisition_id TEXT NOT NULL, approved_revision INTEGER NOT NULL,
                    supplier_id TEXT NOT NULL, total_cents INTEGER NOT NULL,
                    offline_only INTEGER NOT NULL DEFAULT 1);
                INSERT INTO offline_po_drafts VALUES
                  ('po-a2','a','req-2',3,'fictional-supplier',450,1),
                  ('po-b','b','req-0',2,'fictional-other',999,1),
                  ('po-a1','a','req-1',2,'fictional-supplier',125,1);
            """)

        def tearDown(self):
            self.db.close()

        def test_scoped_ordered_projection(self):
            self.assertEqual(list_offline_drafts(self.db, venue_id='a'), [
                ('po-a1','req-1',2,'fictional-supplier',125),
                ('po-a2','req-2',3,'fictional-supplier',450)])
            self.assertEqual(len(list_offline_drafts(self.db, venue_id='b')), 1)
            self.assertEqual(list_offline_drafts(self.db, venue_id='missing'), [])

        def test_missing_venue_fails_closed_without_writes(self):
            for venue in ('', '  ', None):
                with self.assertRaises(ValueError):
                    list_offline_drafts(self.db, venue_id=venue)
            self.assertEqual(self.db.execute(
                'SELECT COUNT(*) FROM offline_po_drafts').fetchone()[0], 3)

    unittest.main()
