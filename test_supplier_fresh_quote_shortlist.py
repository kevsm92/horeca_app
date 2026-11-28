"""Synthetic-only regression tests for advisory fresh quote shortlist."""
import sqlite3
import unittest

from supplier_directory import initialize, add_supplier, add_sku
from supplier_price_history import initialize_history, record_price_revision
from supplier_fresh_quote_shortlist import fresh_quote_shortlist

NOW = '2026-11-21T12:00:00Z'


class FreshQuoteShortlistTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        initialize(self.db)
        for venue in ('a', 'b'):
            for supplier in ('v1', 'v2', 'v3'):
                add_supplier(self.db, venue, supplier, 'Synthetic '+supplier)
                add_sku(self.db, venue, supplier, 's', 'flour', 'kg',
                        {'v1': 3, 'v2': 2, 'v3': 4}[supplier],
                        {'v1': 300, 'v2': 200, 'v3': 400}[supplier], 2)
        add_sku(self.db, 'a', 'v1', 'grams', 'flour', 'g', 1000, 1, 0)
        initialize_history(self.db)

    def tearDown(self):
        self.db.close()

    def shortlist(self, venue='a', unit='kg', now=NOW):
        return fresh_quote_shortlist(self.db, venue, 'flour', unit, now, 1)

    def revision(self, supplier, stamp=NOW, venue='a'):
        record_price_revision(self.db, venue, supplier, 's', 999, 'synthetic quote', stamp)

    def test_missing_stale_future_excluded_and_current_included(self):
        self.revision('v1')
        self.revision('v2', '2026-11-19T12:00:00Z')
        self.revision('v3', '2026-11-22T12:00:00Z')
        self.assertEqual(self.shortlist(), [('v1', 's', 300, 3, 2)])

    def test_latest_revision_overrides_prior_current_revision(self):
        self.revision('v1')
        self.revision('v1', '2026-11-19T12:00:00Z')
        self.assertEqual(self.shortlist(), [])

    def test_integer_rational_ties_and_stable_ids(self):
        for supplier in ('v1', 'v2', 'v3'):
            self.revision(supplier)
        self.assertEqual([r[0] for r in self.shortlist()], ['v1', 'v2', 'v3'])
        self.assertEqual(self.shortlist(unit='g'), [])

    def test_venue_isolation_and_inactive_supplier(self):
        self.revision('v1')
        self.assertEqual(self.shortlist('b'), [])
        self.db.execute("UPDATE supplier SET active=0 WHERE venue_id='a' AND supplier_id='v1'")
        self.assertEqual(self.shortlist(), [])

    def test_invalid_policy_even_when_empty(self):
        with self.assertRaises(ValueError):
            fresh_quote_shortlist(self.db, 'a', 'unknown', 'kg', 'invalid', 1)
        with self.assertRaises(ValueError):
            fresh_quote_shortlist(self.db, 'a', 'unknown', 'kg', NOW, True)
        with self.assertRaises(ValueError):
            self.shortlist(unit='pallet')

    def test_read_only_and_directory_price_not_revision_price(self):
        self.revision('v1')
        before = self.db.total_changes
        self.assertEqual(self.shortlist()[0][2], 300)
        self.assertEqual(self.db.total_changes, before)


if __name__ == '__main__':
    unittest.main()
