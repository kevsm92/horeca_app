"""Synthetic SQLite regression tests for offline order consumption event ledger."""
import sqlite3
import unittest

from order_stock_event import initialize, record_order_consumption


class OrderStockEventRegressions(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        initialize(self.db)

    def tearDown(self):
        self.db.close()

    def record(self, **overrides):
        args = dict(venue_id='venue-a', event_id='event-1', order_id='order-1',
                    ingredients={'flour': 250, 'milk': 100})
        args.update(overrides)
        return record_order_consumption(self.db, **args)

    def test_first_event_writes_negative_ingredient_deltas(self):
        self.assertTrue(self.record())
        self.assertEqual(self.db.execute('SELECT ingredient_id, delta_milliunits FROM order_stock_ledger ORDER BY ingredient_id').fetchall(),
                         [('flour', -250), ('milk', -100)])

    def test_identical_retry_is_noop(self):
        self.record()
        self.assertFalse(self.record(ingredients={'milk': 100, 'flour': 250}))
        self.assertEqual(self.db.execute('SELECT count(*) FROM order_stock_ledger').fetchone()[0], 2)

    def test_conflicting_retry_rolls_back_and_preserves_first_event(self):
        self.record()
        with self.assertRaises(ValueError):
            self.record(ingredients={'flour': 251})
        self.assertEqual(self.db.execute('SELECT sum(delta_milliunits) FROM order_stock_ledger').fetchone()[0], -350)
        self.assertFalse(self.db.in_transaction)

    def test_same_event_id_is_isolated_per_venue(self):
        self.record()
        self.assertTrue(self.record(venue_id='venue-b'))
        self.assertEqual(self.db.execute('SELECT count(*) FROM order_stock_events').fetchone()[0], 2)

    def test_event_and_ledger_cannot_be_mutated(self):
        self.record()
        for statement in (
            "UPDATE order_stock_events SET order_id='other' WHERE venue_id='venue-a'",
            "DELETE FROM order_stock_events WHERE venue_id='venue-a'",
            "UPDATE order_stock_ledger SET delta_milliunits=-1 WHERE venue_id='venue-a'",
            "DELETE FROM order_stock_ledger WHERE venue_id='venue-a'",
        ):
            with self.subTest(statement=statement), self.assertRaises(sqlite3.IntegrityError):
                self.db.execute(statement)
            self.db.rollback()

    def test_invalid_quantities_fail_without_side_effects(self):
        for bad in (0, -1, True, 1.5, 1_000_000_001):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                self.record(ingredients={'flour': bad})
        self.assertEqual(self.db.execute('SELECT count(*) FROM order_stock_events').fetchone()[0], 0)

    def test_existing_transaction_is_not_taken_over(self):
        self.db.execute('BEGIN')
        with self.assertRaises(ValueError):
            self.record()
        self.assertTrue(self.db.in_transaction)
        self.db.rollback()


if __name__ == '__main__':
    unittest.main()
