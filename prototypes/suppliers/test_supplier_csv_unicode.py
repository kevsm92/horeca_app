"""Unicode formula-injection regressions for offline supplier CSV (fictional data)."""
import csv
import io
import sqlite3
import unittest

from supplier_directory import initialize, add_supplier, add_sku
from supplier_directory_export import export_supplier_skus_csv, _safe_cell


class UnicodeCsvSafetyTests(unittest.TestCase):
    def test_unicode_leading_whitespace_formula(self):
        for prefix in ('\u00a0', '\u2003', '\ufeff', '\x0b'):
            with self.subTest(prefix=repr(prefix)):
                self.assertEqual(_safe_cell(prefix + '=1+1'), "'" + prefix + '=1+1')

    def test_real_sqlite_export_preserves_escaped_value(self):
        db = sqlite3.connect(':memory:')
        try:
            initialize(db)
            add_supplier(db, 'alpha', 's1', '\u00a0=2+2')
            add_sku(db, 'alpha', 's1', '\ufeff@SUM(1)', 'flour', 'kg', 1, 100, 2)
            rows = list(csv.reader(io.StringIO(export_supplier_skus_csv(db, 'alpha', 'flour'))))
            self.assertEqual(rows[1][1], "'\u00a0=2+2")
            self.assertEqual(rows[1][2], "'\ufeff@SUM(1)")
        finally:
            db.close()


if __name__ == '__main__':
    unittest.main()
