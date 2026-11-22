"""Read one synthetic offline requisition and its lines within a trusted venue.

This is a domain helper, not an HTTP authorization boundary. The caller must
obtain venue_id from an authenticated, authorized server-side principal.
"""
import sqlite3


def get_requisition_detail(connection: sqlite3.Connection, *, venue_id: str,
                           requisition_id: str) -> dict | None:
    if not all(isinstance(x, str) and x.strip() for x in (venue_id, requisition_id)):
        raise ValueError('venue and requisition are required')
    header = connection.execute(
        """SELECT id, supplier_id, requester_id, status, revision, created_at
           FROM purchase_requisitions WHERE venue_id = ? AND id = ?""",
        (venue_id, requisition_id),
    ).fetchone()
    if header is None:
        return None
    lines = connection.execute(
        """SELECT id, sku, quantity, unit_price_cents
           FROM purchase_requisition_lines
           WHERE venue_id = ? AND requisition_id = ? ORDER BY id""",
        (venue_id, requisition_id),
    ).fetchall()
    total = sum(quantity * price for _, _, quantity, price in lines)
    if total > 9_223_372_036_854_775_807:
        raise ValueError('total exceeds signed 64-bit cents')
    return {
        'id': header[0], 'supplier_id': header[1], 'requester_id': header[2],
        'status': header[3], 'revision': header[4], 'created_at': header[5],
        'lines': [dict(id=i, sku=sku, quantity=q, unit_price_cents=p,
                       line_total_cents=q*p) for i, sku, q, p in lines],
        'total_cents': total,
    }


if __name__ == '__main__':
    import unittest

    class RequisitionDetailTests(unittest.TestCase):
        def setUp(self):
            self.db = sqlite3.connect(':memory:')
            self.db.executescript('''
                CREATE TABLE purchase_requisitions (
                    id TEXT PRIMARY KEY, venue_id TEXT, requester_id TEXT,
                    supplier_id TEXT, status TEXT, revision INTEGER, created_at TEXT);
                CREATE TABLE purchase_requisition_lines (
                    id TEXT PRIMARY KEY, requisition_id TEXT, venue_id TEXT,
                    sku TEXT, quantity INTEGER, unit_price_cents INTEGER);
                INSERT INTO purchase_requisitions VALUES
                    ('r1','venue-a','fictional-worker','fictional-supplier','draft',1,'2026-11-22T00:00:00Z'),
                    ('r2','venue-b','other-worker','other-supplier','submitted',2,'2026-11-22T00:00:00Z');
                INSERT INTO purchase_requisition_lines VALUES
                    ('l2','r1','venue-a','water',2,150),
                    ('l1','r1','venue-a','bread',3,200),
                    ('l3','r2','venue-b','secret',1,9999),
                    ('l4','r1','venue-b','injected',1,8888);
            ''')

        def tearDown(self):
            self.db.close()

        def test_scoped_lines_and_integer_totals(self):
            result = get_requisition_detail(self.db, venue_id='venue-a', requisition_id='r1')
            self.assertEqual(result['total_cents'], 900)
            self.assertEqual([x['id'] for x in result['lines']], ['l1','l2'])
            self.assertEqual(result['lines'][0]['line_total_cents'], 600)
            self.assertEqual(result['status'], 'draft')

        def test_cross_venue_and_missing_are_indistinguishable(self):
            self.assertIsNone(get_requisition_detail(self.db, venue_id='venue-a', requisition_id='r2'))
            self.assertIsNone(get_requisition_detail(self.db, venue_id='venue-a', requisition_id='missing'))
            self.assertEqual(get_requisition_detail(self.db, venue_id='venue-b', requisition_id='r2')['total_cents'],9999)

        def test_invalid_scope_fails_closed_and_no_mutation(self):
            for venue, req in [('', 'r1'), (None, 'r1'), ('venue-a', ''), ('venue-a', None)]:
                with self.assertRaises(ValueError):
                    get_requisition_detail(self.db, venue_id=venue, requisition_id=req)
            self.assertEqual(self.db.execute('SELECT COUNT(*) FROM purchase_requisition_lines').fetchone()[0],4)

    unittest.main()
