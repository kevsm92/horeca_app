"""Synthetic tests: python -m unittest discover -s prototypes/inventory -p 'test_*.py'."""
import sqlite3
import unittest
from inventory_ledger import initialize, add_ingredient, post_event
from inventory_sqlite_reconcile import reconcile_sqlite


class SQLiteReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:', isolation_level=None)
        initialize(self.db)
        for venue in ('north', 'south'):
            add_ingredient(self.db, venue, 'flour', 'Flour', 'g')
        add_ingredient(self.db, 'north', 'oil', 'Oil', 'ml')

    def tearDown(self):
        self.db.close()

    def test_zero_stock_and_venue_isolation(self):
        post_event(self.db, 'south', 'flour', 'r1', 900, 'receipt')
        self.assertEqual(reconcile_sqlite(self.db, 'north'), {'flour': 0, 'oil': 0})
        self.assertEqual(reconcile_sqlite(self.db, 'south'), {'flour': 900})

    def test_ordered_receipt_use_waste(self):
        post_event(self.db, 'north', 'flour', 'r', 100, 'receipt')
        post_event(self.db, 'north', 'flour', 'u', -40, 'use')
        post_event(self.db, 'north', 'flour', 'w', -10, 'waste')
        self.assertEqual(reconcile_sqlite(self.db, 'north')['flour'], 50)

    def test_retry_is_not_double_counted(self):
        post_event(self.db, 'north', 'flour', 'r', 100, 'receipt')
        self.assertFalse(post_event(self.db, 'north', 'flour', 'r', 100, 'receipt'))
        self.assertEqual(reconcile_sqlite(self.db, 'north')['flour'], 100)

    def test_invalid_venue_rejected(self):
        for value in ('', None, 12):
            with self.assertRaises(ValueError):
                reconcile_sqlite(self.db, value)

    def test_reader_does_not_write(self):
        post_event(self.db, 'north', 'flour', 'r', 5, 'receipt')
        before = self.db.total_changes
        reconcile_sqlite(self.db, 'north')
        self.assertEqual(self.db.total_changes, before)

    def test_corrupt_negative_history_detected(self):
        self.db.execute("DROP TRIGGER stock_no_update")
        self.db.execute("DROP TRIGGER stock_no_delete")
        self.db.execute(
            "INSERT INTO stock_events(venue_id,event_id,ingredient_id,delta,reason) "
            "VALUES(?,?,?,?,?)", ('north','bad','flour',-2,'use')
        )
        with self.assertRaisesRegex(ValueError, 'negative stock'):
            reconcile_sqlite(self.db, 'north')


if __name__ == '__main__':
    unittest.main()
