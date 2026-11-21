"""Regression gates for the offline supplier CSV preview (synthetic records only)."""
import csv
import io
import sqlite3
import unittest
from supplier_directory import initialize, add_supplier, add_sku
from supplier_directory_export import export_supplier_skus_csv, HEADERS


class SupplierCsvSecurityTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        initialize(self.db)
        for venue in ('alpha', 'beta'):
            add_supplier(self.db, venue, 'v1', '=HYPERLINK("https://invalid.example")')
            add_sku(self.db, venue, 'v1', '@SUM(1,2)', 'flour', 'kg', 2, 300, 3)
        add_supplier(self.db, 'alpha', 'inactive', '+CMD')
        add_sku(self.db, 'alpha', 'inactive', '-bad', 'flour', 'kg', 1, 1, 0)
        self.db.execute("UPDATE supplier SET active=0 WHERE venue_id='alpha' AND supplier_id='inactive'")
        add_sku(self.db, 'alpha', 'v1', 'other', 'milk', 'l', 1, 100, 1)

    def tearDown(self):
        self.db.close()

    def test_formula_cells_are_escaped_and_csv_remains_parseable(self):
        text = export_supplier_skus_csv(self.db, 'alpha', 'flour')
        rows = list(csv.reader(io.StringIO(text)))
        self.assertEqual(tuple(rows[0]), HEADERS)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1][1], "'=HYPERLINK(\"https://invalid.example\")")
        self.assertEqual(rows[1][2], "'@SUM(1,2)")
        self.assertEqual(rows[1][5], '300')
        self.assertTrue(text.endswith('\r\n'))

    def test_inactive_and_other_ingredient_excluded(self):
        rows = list(csv.reader(io.StringIO(export_supplier_skus_csv(self.db, 'alpha', 'flour'))))
        self.assertEqual([r[2] for r in rows[1:]], ["'@SUM(1,2)"])

    def test_unknown_venue_and_ingredient_return_header_only(self):
        for venue, ingredient in [('missing', 'flour'), ('alpha', 'missing')]:
            self.assertEqual(list(csv.reader(io.StringIO(export_supplier_skus_csv(self.db, venue, ingredient)))), [list(HEADERS)])

    def test_invalid_scope_rejected(self):
        for venue, ingredient in [('', 'flour'), ('alpha', ' '), (None, 'flour'), ('alpha', None)]:
            with self.subTest(venue=venue, ingredient=ingredient), self.assertRaises(ValueError):
                export_supplier_skus_csv(self.db, venue, ingredient)


if __name__ == '__main__':
    unittest.main()
