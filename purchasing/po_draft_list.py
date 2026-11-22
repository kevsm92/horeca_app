"""Read-only, venue-scoped offline purchase-order draft index.

The venue_id MUST come from authenticated server context, not request parameters.
This domain function does not implement authentication or RBAC. No orders are sent.
"""
import sqlite3


def list_offline_po_drafts(connection: sqlite3.Connection, *, venue_id: str,
                           limit: int = 50) -> list[dict]:
    if not isinstance(venue_id, str) or not venue_id.strip():
        raise ValueError('authenticated venue scope required')
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError('limit must be an integer from 1 to 100')
    rows = connection.execute(
        """SELECT id, requisition_id, approved_revision, supplier_id, total_cents
           FROM offline_po_drafts
           WHERE venue_id = ? AND offline_only = 1
           ORDER BY id ASC LIMIT ?""", (venue_id, limit),
    ).fetchall()
    return [dict(id=row[0], requisition_id=row[1], approved_revision=row[2],
                 supplier_id=row[3], total_cents=row[4], currency='EUR',
                 offline_only=True) for row in rows]


if __name__ == '__main__':
    import unittest

    class DraftIndexTests(unittest.TestCase):
        def setUp(self):
            self.db = sqlite3.connect(':memory:')
            self.db.executescript("""
                CREATE TABLE offline_po_drafts (
                    id TEXT PRIMARY KEY, venue_id TEXT, requisition_id TEXT,
                    approved_revision INTEGER, supplier_id TEXT,
                    total_cents INTEGER, offline_only INTEGER);
                INSERT INTO offline_po_drafts VALUES
                    ('a2','venue-a','req2',2,'fictional-b',2000,1),
                    ('a1','venue-a','req1',1,'fictional-a',500,1),
                    ('a3','venue-a','req3',3,'fictional-c',300,0),
                    ('b1','venue-b','req4',1,'fictional-d',9000,1);
            """)

        def tearDown(self):
            self.db.close()

        def test_index_is_ordered_and_offline_only(self):
            result = list_offline_po_drafts(self.db, venue_id='venue-a')
            self.assertEqual([item['id'] for item in result], ['a1', 'a2'])
            self.assertEqual(result[0]['total_cents'], 500)
            self.assertTrue(all(item['offline_only'] for item in result))

        def test_cross_venue_isolation_and_unknown_scope(self):
            self.assertEqual([x['id'] for x in list_offline_po_drafts(self.db, venue_id='venue-b')], ['b1'])
            self.assertEqual(list_offline_po_drafts(self.db, venue_id='unknown'), [])

        def test_limit_and_scope_validation(self):
            self.assertEqual(len(list_offline_po_drafts(self.db, venue_id='venue-a', limit=1)), 1)
            for scope in ('', ' ', None, 5):
                with self.assertRaises(ValueError):
                    list_offline_po_drafts(self.db, venue_id=scope)
            for bad in (0, 101, True, 1.5, '2'):
                with self.assertRaises(ValueError):
                    list_offline_po_drafts(self.db, venue_id='venue-a', limit=bad)

        def test_read_only(self):
            before = self.db.total_changes
            list_offline_po_drafts(self.db, venue_id='venue-a')
            self.assertEqual(self.db.total_changes, before)

    unittest.main()
