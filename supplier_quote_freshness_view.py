"""Read-only supplier quote freshness advisory; no orders or external I/O.

History records do not automatically update supplier_sku prices. A revision
is shown as evidence only, never as proof the current price was confirmed.
"""
from supplier_directory import list_skus
from supplier_quote_age import quote_age_status


def supplier_quote_freshness(db, venue_id, ingredient_id, as_of, max_age_days):
    """Return per-SKU (supplier, sku, price_cents, status, recorded_at).

    Missing history is 'unverified', not 'current'. Latest revision uses
    revision sequence, not untrusted timestamps. Current SKU prices remain
    independent of historical revision prices.
    """
    quote_age_status(as_of, as_of, max_age_days)
    result = []
    for supplier, _name, sku, _unit, _qty, cents, _lead in list_skus(db, venue_id, ingredient_id):
        revision = db.execute('''SELECT recorded_at FROM supplier_price_revision
            WHERE venue_id=? AND supplier_id=? AND sku=?
            ORDER BY revision DESC LIMIT 1''', (venue_id, supplier, sku)).fetchone()
        stamp = revision[0] if revision else None
        status = quote_age_status(stamp, as_of, max_age_days) if stamp else 'unverified'
        result.append((supplier, sku, cents, status, stamp))
    return result


if __name__ == '__main__':
    import sqlite3
    import unittest
    from supplier_directory import initialize, add_supplier, add_sku
    from supplier_price_history import initialize_history, record_price_revision

    class FreshnessViewTests(unittest.TestCase):
        def setUp(self):
            self.db = sqlite3.connect(':memory:')
            initialize(self.db)
            for venue in ('a', 'b'):
                add_supplier(self.db, venue, 'v', 'Fictional Vendor')
                add_sku(self.db, venue, 'v', 's', 'flour', 'kg', 1, 100, 2)
            initialize_history(self.db)

        def tearDown(self):
            self.db.close()

        def view(self, venue='a', now='2026-11-21T12:00:00Z', days=1):
            return supplier_quote_freshness(self.db, venue, 'flour', now, days)

        def test_missing_revision_is_unverified(self):
            self.assertEqual(self.view(), [('v', 's', 100, 'unverified', None)])

        def test_stale_and_current_and_future(self):
            record_price_revision(self.db, 'a', 'v', 's', 120, 'fictional', '2026-11-19T12:00:00Z')
            self.assertEqual(self.view()[0][3], 'stale')
            record_price_revision(self.db, 'a', 'v', 's', 130, 'fictional', '2026-11-21T12:00:00Z')
            self.assertEqual(self.view()[0][3], 'current')
            self.assertEqual(self.view(now='2026-11-20T12:00:00Z')[0][3], 'future')

        def test_tenant_isolation_and_price_not_overwritten(self):
            record_price_revision(self.db, 'a', 'v', 's', 999, 'fictional', '2026-11-21T12:00:00Z')
            self.assertEqual(self.view('b')[0][3], 'unverified')
            self.assertEqual(self.view('a')[0][2], 100)

        def test_invalid_policy_even_when_no_quotes(self):
            with self.assertRaises(ValueError):
                supplier_quote_freshness(self.db, 'a', 'missing', 'bad', 1)
            with self.assertRaises(ValueError):
                self.view(days=True)

        def test_inactive_supplier_excluded(self):
            self.db.execute("UPDATE supplier SET active=0 WHERE venue_id='a'")
            self.assertEqual(self.view(), [])

    unittest.main()
