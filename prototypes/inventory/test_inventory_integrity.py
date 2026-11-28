"""Balance integrity regression checks for venue-scoped inventory ledger.

Run: python -m unittest discover -s prototypes/inventory -p 'test_inventory_integrity.py' -v
Synthetic data only; no services or network.
"""
import importlib.util
import sqlite3
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("inventory_ledger", Path(__file__).with_name("inventory_ledger.py"))
ledger = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ledger)


class BalanceIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:", isolation_level=None)
        ledger.initialize(self.db)
        ledger.add_ingredient(self.db, "north", "milk", "Synthetic milk", "ml")
        ledger.add_ingredient(self.db, "south", "milk", "Synthetic milk", "ml")

    def tearDown(self):
        self.db.close()

    def test_balance_matches_immutable_event_sum_across_venues(self):
        for venue, event, amount, reason in [
            ("north", "r1", 500, "receipt"),
            ("north", "u1", -120, "use"),
            ("north", "w1", -30, "waste"),
            ("south", "r1", 80, "receipt"),
        ]:
            self.assertTrue(ledger.post_event(self.db, venue, "milk", event, amount, reason))
        for venue, expected in [("north", 350), ("south", 80)]:
            aggregate = self.db.execute(
                "SELECT COALESCE(SUM(delta),0) FROM stock_events WHERE venue_id=? AND ingredient_id=?",
                (venue, "milk"),
            ).fetchone()[0]
            self.assertEqual(ledger.balance(self.db, venue, "milk"), expected)
            self.assertEqual(aggregate, expected)

    def test_failed_deduction_preserves_ledger_and_balance(self):
        ledger.post_event(self.db, "north", "milk", "receipt", 20, "receipt")
        before = self.db.execute("SELECT COUNT(*), SUM(delta) FROM stock_events").fetchone()
        with self.assertRaisesRegex(ValueError, "insufficient stock"):
            ledger.post_event(self.db, "north", "milk", "too-much", -21, "use")
        self.assertEqual(self.db.execute("SELECT COUNT(*), SUM(delta) FROM stock_events").fetchone(), before)
        self.assertEqual(ledger.balance(self.db, "north", "milk"), 20)
        self.assertTrue(ledger.post_event(self.db, "north", "milk", "valid-after-failure", -20, "use"))
        self.assertEqual(ledger.balance(self.db, "north", "milk"), 0)

    def test_conflicting_retry_does_not_change_existing_aggregate(self):
        ledger.post_event(self.db, "north", "milk", "same", 50, "receipt")
        with self.assertRaisesRegex(ValueError, "conflicting idempotency key"):
            ledger.post_event(self.db, "north", "milk", "same", 51, "receipt")
        self.assertEqual(ledger.balance(self.db, "north", "milk"), 50)
        self.assertEqual(self.db.execute(
            "SELECT COUNT(*) FROM stock_events WHERE venue_id='north'"
        ).fetchone()[0], 1)

    def test_unknown_ingredient_does_not_silently_report_zero(self):
        with self.assertRaisesRegex(ValueError, "ingredient not found"):
            ledger.balance(self.db, "north", "missing")
        self.assertEqual(ledger.balance(self.db, "south", "milk"), 0)


if __name__ == "__main__":
    unittest.main()
