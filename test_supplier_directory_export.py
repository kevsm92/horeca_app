import csv
import io
import sqlite3
import unittest
from supplier_directory import initialize, add_supplier, add_sku
from supplier_directory_export import export_supplier_skus_csv, HEADERS

class SupplierDirectoryExportTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        initialize(self.db)
        add_supplier(self.db, 'a', 's1', '=HYPERLINK("bad")')
        add_supplier(self.db, 'b', 's1', 'Other venue')
        add_sku(self.db, 'a', 's1', '@SKU', 'flour', 'kg', 2, 499, 3)
        add_sku(self.db, 'b', 's1', 'other', 'flour', 'kg', 1, 999, 4)

    def tearDown(self):
        self.db.close()

    def test_venue_scoped_and_formula_safe(self):
        rows = list(csv.reader(io.StringIO(export_supplier_skus_csv(self.db, 'a', 'flour'))))
        self.assertEqual(tuple(rows[0]), HEADERS)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1], ['s1', '\'=HYPERLINK("bad")', "'@SKU", 'kg', '2', '499', '3'])
        self.assertNotIn('999', str(rows))

    def test_inactive_excluded_and_empty_header(self):
        self.db.execute('UPDATE supplier SET active=0 WHERE venue_id=?', ('a',))
        self.assertEqual(list(csv.reader(io.StringIO(export_supplier_skus_csv(self.db, 'a', 'flour')))), [list(HEADERS)])

    def test_reject_missing_scope(self):
        for venue, ingredient in [('', 'flour'), ('a', ''), (None, 'flour'), ('a', None)]:
            with self.assertRaises(ValueError):
                export_supplier_skus_csv(self.db, venue, ingredient)

    def test_read_only_and_crlf(self):
        before = self.db.total_changes
        result = export_supplier_skus_csv(self.db, 'a', 'flour')
        self.assertEqual(self.db.total_changes, before)
        self.assertIn('\r\n', result)

if __name__ == '__main__':
    unittest.main()
