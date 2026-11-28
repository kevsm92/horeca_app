"""Venue-scoped read of an offline purchase-order draft; never transmits orders.

Caller must supply venue_id from an authenticated and authorized server context.
This is a domain helper, not an HTTP authentication or RBAC boundary.
"""
import sqlite3


def get_offline_po_draft(connection: sqlite3.Connection, *, venue_id: str,
                         draft_id: str) -> dict | None:
    if not all(isinstance(v, str) and v.strip() for v in (venue_id, draft_id)):
        raise ValueError('venue and draft are required')
    row = connection.execute(
        """SELECT d.id, d.requisition_id, d.approved_revision, d.supplier_id,
                  d.total_cents, d.offline_only
           FROM offline_po_drafts d
           WHERE d.id = ? AND d.venue_id = ?""", (draft_id, venue_id),
    ).fetchone()
    if row is None:
        return None
    if row[5] != 1:
        raise ValueError('draft is not offline-only')
    return dict(id=row[0], requisition_id=row[1], approved_revision=row[2],
                supplier_id=row[3], total_cents=row[4], currency='EUR',
                offline_only=True)


if __name__ == '__main__':
    import unittest

    class DraftDetailTests(unittest.TestCase):
        def setUp(self):
            self.db = sqlite3.connect(':memory:')
            self.db.executescript("""
                CREATE TABLE offline_po_drafts (
                    id TEXT PRIMARY KEY, venue_id TEXT, requisition_id TEXT,
                    approved_revision INTEGER, supplier_id TEXT,
                    total_cents INTEGER, offline_only INTEGER);
                INSERT INTO offline_po_drafts VALUES
                    ('d1','venue-a','r1',3,'fictional-supplier',850,1),
                    ('d2','venue-b','r2',2,'other-supplier',9900,1);
            """)

        def tearDown(self):
            self.db.close()

        def test_read_offline_draft(self):
            self.assertEqual(get_offline_po_draft(self.db, venue_id='venue-a', draft_id='d1'),
                             dict(id='d1', requisition_id='r1', approved_revision=3,
                                  supplier_id='fictional-supplier', total_cents=850,
                                  currency='EUR', offline_only=True))

        def test_cross_venue_and_unknown_are_indistinguishable(self):
            self.assertIsNone(get_offline_po_draft(self.db, venue_id='venue-a', draft_id='d2'))
            self.assertIsNone(get_offline_po_draft(self.db, venue_id='venue-a', draft_id='missing'))

        def test_invalid_scope_and_nonoffline_fail_closed(self):
            for venue, draft in [('', 'd1'), (None, 'd1'), ('venue-a', ''), ('venue-a', None)]:
                with self.assertRaises(ValueError):
                    get_offline_po_draft(self.db, venue_id=venue, draft_id=draft)
            self.db.execute("UPDATE offline_po_drafts SET offline_only=0 WHERE id='d1'")
            with self.assertRaises(ValueError):
                get_offline_po_draft(self.db, venue_id='venue-a', draft_id='d1')

        def test_read_does_not_mutate(self):
            before = self.db.total_changes
            get_offline_po_draft(self.db, venue_id='venue-a', draft_id='d1')
            self.assertEqual(self.db.total_changes, before)

    unittest.main()
