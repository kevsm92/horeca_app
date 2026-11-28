"""Read-only ledger integrity checks for synthetic offline HORECA inventory.

Run: python -m unittest test_stock_integrity.py -v
This is a diagnostic, not an authorization or tamper-proofing mechanism.
"""
import sqlite3
import unittest


def audit_stock(db, venue_id):
    """Return sorted (ingredient_id, balance, issue) tuples for one venue.

    This never mutates inventory. Negative totals and orphan events are flagged.
    """
    if not isinstance(venue_id, str) or not venue_id or len(venue_id) > 100:
        raise ValueError('invalid venue')
    ingredients = db.execute(
        'SELECT ingredient_id FROM ingredients WHERE venue_id=?', (venue_id,)
    ).fetchall()
    findings = []
    for (ingredient_id,) in ingredients:
        total = db.execute(
            'SELECT COALESCE(SUM(delta),0) FROM stock_events '
            'WHERE venue_id=? AND ingredient_id=?', (venue_id, ingredient_id)
        ).fetchone()[0]
        if total < 0:
            findings.append((ingredient_id, total, 'negative_balance'))
    orphans = db.execute(
        'SELECT e.ingredient_id, SUM(e.delta) FROM stock_events e '
        'LEFT JOIN ingredients i ON i.venue_id=e.venue_id '
        'AND i.ingredient_id=e.ingredient_id '
        'WHERE e.venue_id=? AND i.ingredient_id IS NULL '
        'GROUP BY e.ingredient_id', (venue_id,)
    ).fetchall()
    findings.extend((ingredient_id, total, 'orphan_events') for ingredient_id, total in orphans)
    return sorted(findings)


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.executescript('''
        CREATE TABLE ingredients(venue_id TEXT, ingredient_id TEXT);
        CREATE TABLE stock_events(venue_id TEXT, ingredient_id TEXT, delta INTEGER);
        INSERT INTO ingredients VALUES ('a','flour'),('a','milk'),('b','flour');
        INSERT INTO stock_events VALUES ('a','flour',10),('a','flour',-3),
          ('b','flour',-20);
        ''')
    def tearDown(self):
        self.db.close()
    def test_valid_balances_no_findings(self):
        self.assertEqual(audit_stock(self.db, 'a'), [])
    def test_negative_balance_detected(self):
        self.assertEqual(audit_stock(self.db, 'b'), [('flour', -20, 'negative_balance')])
    def test_orphan_detected(self):
        self.db.execute("INSERT INTO stock_events VALUES ('a','ghost',4)")
        self.assertEqual(audit_stock(self.db, 'a'), [('ghost', 4, 'orphan_events')])
    def test_venue_isolation(self):
        self.assertEqual(audit_stock(self.db, 'a'), [])
    def test_read_only(self):
        before = self.db.total_changes
        audit_stock(self.db, 'b')
        self.assertEqual(self.db.total_changes, before)
    def test_invalid_venue(self):
        for venue in ('', None, 'x'*101):
            with self.assertRaises(ValueError):
                audit_stock(self.db, venue)


if __name__ == '__main__':
    unittest.main()
