"""Read-only purchasing approval queue for an authenticated venue manager.

Caller MUST enforce manager purchasing RBAC and derive venue_id from session.
No orders are sent, and this module is not an HTTP authorization boundary.
"""
import sqlite3


def list_submitted_for_approval(connection: sqlite3.Connection, *, venue_id: str,
                                approver_id: str, limit: int = 50) -> list[dict]:
    """List submitted requisitions eligible for independent manager review.

    Excludes the approver's own requests; approval remains a separate CAS operation.
    """
    if not isinstance(venue_id, str) or not venue_id.strip():
        raise ValueError('authenticated venue scope required')
    if not isinstance(approver_id, str) or not approver_id.strip():
        raise ValueError('authenticated approver required')
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError('limit must be an integer from 1 to 100')
    rows = connection.execute(
        """SELECT r.id, r.requester_id, r.supplier_id, r.revision,
                  r.created_at, SUM(l.quantity * l.unit_price_cents) AS total_cents
           FROM purchase_requisitions AS r
           JOIN purchase_requisition_lines AS l
             ON l.requisition_id = r.id AND l.venue_id = r.venue_id
           WHERE r.venue_id = ? AND r.status = 'submitted'
             AND r.requester_id <> ?
           GROUP BY r.id, r.requester_id, r.supplier_id, r.revision, r.created_at
           ORDER BY r.created_at ASC, r.id ASC LIMIT ?""",
        (venue_id, approver_id, limit),
    ).fetchall()
    return [dict(id=r[0], requester_id=r[1], supplier_id=r[2],
                 revision=r[3], created_at=r[4], total_cents=r[5],
                 currency='EUR') for r in rows]


if __name__ == '__main__':
    import unittest

    class ApprovalQueueTests(unittest.TestCase):
        def setUp(self):
            self.db = sqlite3.connect(':memory:')
            self.db.executescript("""
                CREATE TABLE purchase_requisitions (
                    id TEXT PRIMARY KEY, venue_id TEXT NOT NULL,
                    requester_id TEXT NOT NULL, supplier_id TEXT NOT NULL,
                    status TEXT NOT NULL, revision INTEGER NOT NULL,
                    created_at TEXT NOT NULL);
                CREATE TABLE purchase_requisition_lines (
                    id TEXT PRIMARY KEY, requisition_id TEXT NOT NULL,
                    venue_id TEXT NOT NULL, sku TEXT NOT NULL,
                    quantity INTEGER NOT NULL, unit_price_cents INTEGER NOT NULL);
                INSERT INTO purchase_requisitions VALUES
                  ('a1','a','staff','synthetic-supplier','submitted',2,'2026-11-22T08:00:00Z'),
                  ('a2','a','manager','synthetic-supplier','submitted',2,'2026-11-22T08:01:00Z'),
                  ('a3','a','staff','synthetic-supplier','draft',1,'2026-11-22T08:02:00Z'),
                  ('b1','b','staff','synthetic-supplier','submitted',2,'2026-11-22T07:00:00Z');
                INSERT INTO purchase_requisition_lines VALUES
                  ('l1','a1','a','s1',2,125),('l2','a1','a','s2',3,100),
                  ('l3','a2','a','s3',1,800),('l4','a3','a','s4',1,100),
                  ('l5','b1','b','s5',1,9999),
                  ('l6','a1','b','wrong-venue',1,99999);
            """)

        def tearDown(self):
            self.db.close()

        def test_eligible_only_and_integer_cents(self):
            rows = list_submitted_for_approval(self.db, venue_id='a', approver_id='manager')
            self.assertEqual([r['id'] for r in rows], ['a1'])
            self.assertEqual(rows[0]['total_cents'], 550)
            self.assertEqual(rows[0]['revision'], 2)

        def test_venue_isolation_and_separation(self):
            self.assertEqual([r['id'] for r in list_submitted_for_approval(
                self.db, venue_id='b', approver_id='manager')], ['b1'])
            self.assertEqual([r['id'] for r in list_submitted_for_approval(
                self.db, venue_id='a', approver_id='staff')], ['a2'])

        def test_validation_and_limit(self):
            self.assertEqual(len(list_submitted_for_approval(
                self.db, venue_id='a', approver_id='external', limit=1)), 1)
            for value in ('', ' ', None, 1):
                with self.assertRaises(ValueError):
                    list_submitted_for_approval(self.db, venue_id=value, approver_id='manager')
                with self.assertRaises(ValueError):
                    list_submitted_for_approval(self.db, venue_id='a', approver_id=value)
            for value in (0, 101, True, '5'):
                with self.assertRaises(ValueError):
                    list_submitted_for_approval(self.db, venue_id='a', approver_id='manager', limit=value)

        def test_read_only(self):
            before = self.db.total_changes
            list_submitted_for_approval(self.db, venue_id='a', approver_id='manager')
            self.assertEqual(self.db.total_changes, before)

    unittest.main()
