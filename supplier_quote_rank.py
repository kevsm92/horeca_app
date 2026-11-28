"""Offline exact-unit supplier quote ranking; no orders or external I/O.

Only compares offers sharing the same physical unit. Cross-unit conversion
(e.g. kg vs g) requires an explicitly approved conversion policy.
"""
from functools import cmp_to_key

from supplier_directory import list_skus


def rank_supplier_quotes(db, venue_id, ingredient_id, unit):
    """Return (supplier_id, name, sku, unit, pack_qty, cents, lead_days).

    Compare cents per declared unit by integer cross-multiplication, then
    lead time and stable identifiers. Never use floating-point money.
    """
    if unit not in ('g', 'kg', 'ml', 'l', 'each'):
        raise ValueError('recognized exact unit required')
    rows = [r for r in list_skus(db, venue_id, ingredient_id) if r[3] == unit]
    def compare(a, b):
        left = a[5] * b[4]
        right = b[5] * a[4]
        return (left > right) - (left < right) or (a[6] > b[6]) - (a[6] < b[6]) or ((a[0], a[2]) > (b[0], b[2])) - ((a[0], a[2]) < (b[0], b[2]))
    return sorted(rows, key=cmp_to_key(compare))


if __name__ == '__main__':
    import unittest
    import sqlite3
    from supplier_directory import initialize, add_supplier, add_sku

    class QuoteRankTests(unittest.TestCase):
        def setUp(self):
            self.db = sqlite3.connect(':memory:')
            initialize(self.db)
            for venue in ('a', 'b'):
                for vendor in ('v1', 'v2', 'v3'):
                    add_supplier(self.db, venue, vendor, 'Fictional ' + vendor)
            add_sku(self.db, 'a', 'v1', 's1', 'flour', 'kg', 3, 301, 2)
            add_sku(self.db, 'a', 'v2', 's2', 'flour', 'kg', 2, 200, 3)
            add_sku(self.db, 'a', 'v3', 's3', 'flour', 'kg', 4, 400, 1)
            add_sku(self.db, 'a', 'v1', 'grams', 'flour', 'g', 1000, 1, 0)
            add_sku(self.db, 'b', 'v1', 'other', 'flour', 'kg', 1, 1, 0)

        def tearDown(self):
            self.db.close()

        def test_exact_rational_ranking_and_tie_break(self):
            self.assertEqual([r[2] for r in rank_supplier_quotes(self.db, 'a', 'flour', 'kg')], ['s3', 's2', 's1'])

        def test_no_cross_unit_or_cross_venue_leak(self):
            self.assertEqual([r[2] for r in rank_supplier_quotes(self.db, 'a', 'flour', 'g')], ['grams'])
            self.assertEqual([r[2] for r in rank_supplier_quotes(self.db, 'b', 'flour', 'kg')], ['other'])

        def test_invalid_unit_and_missing_ingredient(self):
            with self.assertRaises(ValueError):
                rank_supplier_quotes(self.db, 'a', 'flour', 'box')
            self.assertEqual(rank_supplier_quotes(self.db, 'a', 'unknown', 'kg'), [])

    unittest.main()
