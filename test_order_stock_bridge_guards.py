"""Regression: the trusted order bridge rejects unsafe snapshots before ledger writes.

Run: python -m unittest test_order_stock_bridge_guards.py
Synthetic fixtures only; no HTTP, payment, or live KDS.
"""
import sqlite3
import unittest

from order_stock_bridge import consume_finalized_order
from order_stock_event import initialize
from prototypes.stock_event import Deduction


class OrderStockBridgeGuardTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        initialize(self.db)
        self.recipes = {"dish-1": (Deduction("flour", 125),)}
        self.order = {
            "id": "order-1", "venue_id": "venue-a",
            "status": "finalized", "lines": (("dish-1", 2),),
        }

    def tearDown(self):
        self.db.close()

    def assert_empty(self):
        self.assertEqual(self.db.execute("SELECT count(*) FROM order_stock_events").fetchone()[0], 0)
        self.assertEqual(self.db.execute("SELECT count(*) FROM order_stock_ledger").fetchone()[0], 0)

    def test_rejects_cross_venue_snapshot_without_mutation(self):
        with self.assertRaisesRegex(ValueError, "venue mismatch"):
            consume_finalized_order(self.db, venue_id="venue-b", order=self.order, recipes=self.recipes)
        self.assert_empty()

    def test_rejects_nonfinal_statuses_without_mutation(self):
        for status in ("accepted", "cancelled", "voided", None):
            with self.subTest(status=status):
                with self.assertRaisesRegex(ValueError, "not finalized"):
                    consume_finalized_order(
                        self.db, venue_id="venue-a",
                        order={**self.order, "status": status}, recipes=self.recipes,
                    )
                self.assert_empty()

    def test_rejects_missing_recipe_without_mutation(self):
        with self.assertRaisesRegex(ValueError, "recipe missing"):
            consume_finalized_order(self.db, venue_id="venue-a", order=self.order, recipes={})
        self.assert_empty()

    def test_finalized_snapshot_deducts_once(self):
        self.assertTrue(consume_finalized_order(
            self.db, venue_id="venue-a", order=self.order, recipes=self.recipes))
        self.assertFalse(consume_finalized_order(
            self.db, venue_id="venue-a", order=self.order, recipes=self.recipes))
        self.assertEqual(self.db.execute(
            "SELECT ingredient_id, delta_milliunits FROM order_stock_ledger").fetchall(),
            [("flour", -250)])


if __name__ == "__main__":
    unittest.main()
