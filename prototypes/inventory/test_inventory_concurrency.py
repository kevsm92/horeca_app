"""Concurrency regression tests for the offline SQLite inventory ledger.

Run from repository root:
  python -m unittest discover -s prototypes/inventory -p 'test_inventory_concurrency.py' -v
Uses only synthetic data and Python's standard library.
"""
import importlib.util
import os
import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path

MODULE = Path(__file__).with_name("inventory_ledger.py")
spec = importlib.util.spec_from_file_location("inventory_ledger", MODULE)
ledger = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ledger)


class ConcurrentLedgerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "stock.sqlite3")
        with self.connect() as db:
            ledger.initialize(db)
            ledger.add_ingredient(db, "venue-a", "flour", "Synthetic flour", "g")
            ledger.add_ingredient(db, "venue-b", "flour", "Synthetic flour", "g")
            ledger.post_event(db, "venue-a", "flour", "initial", 10, "receipt")

    def tearDown(self):
        self.tmp.cleanup()

    def connect(self):
        db = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        db.execute("PRAGMA busy_timeout=10000")
        db.execute("PRAGMA foreign_keys=ON")
        return db

    def race(self, actions):
        gate = threading.Barrier(len(actions))
        results = [None] * len(actions)

        def worker(index, action):
            try:
                with self.connect() as db:
                    gate.wait(timeout=5)
                    results[index] = ("ok", action(db))
            except Exception as exc:
                results[index] = ("error", type(exc).__name__, str(exc))

        threads = [threading.Thread(target=worker, args=(i, action))
                   for i, action in enumerate(actions)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=15)
        self.assertTrue(all(not thread.is_alive() for thread in threads),
                        "SQLite worker did not finish")
        self.assertTrue(all(result is not None for result in results))
        return results

    def test_competing_deductions_cannot_oversell(self):
        actions = [
            lambda db, i=i: ledger.post_event(
                db, "venue-a", "flour", f"use-{i}", -7, "use")
            for i in range(2)
        ]
        results = self.race(actions)
        self.assertEqual(sum(r == ("ok", True) for r in results), 1, results)
        self.assertEqual(sum(r[0] == "error" and r[1] == "ValueError"
                             for r in results), 1, results)
        with self.connect() as db:
            self.assertEqual(ledger.balance(db, "venue-a", "flour"), 3)

    def test_same_event_id_is_applied_once(self):
        actions = [
            lambda db: ledger.post_event(
                db, "venue-a", "flour", "once", -4, "use")
            for _ in range(3)
        ]
        results = self.race(actions)
        self.assertEqual(sum(r == ("ok", True) for r in results), 1, results)
        self.assertEqual(sum(r == ("ok", False) for r in results), 2, results)
        with self.connect() as db:
            self.assertEqual(ledger.balance(db, "venue-a", "flour"), 6)

    def test_simultaneous_venues_remain_isolated(self):
        actions = [
            lambda db: ledger.post_event(
                db, "venue-a", "flour", "shared", -3, "use"),
            lambda db: ledger.post_event(
                db, "venue-b", "flour", "shared", 8, "receipt"),
        ]
        self.assertEqual(self.race(actions), [("ok", True), ("ok", True)])
        with self.connect() as db:
            self.assertEqual(ledger.balance(db, "venue-a", "flour"), 7)
            self.assertEqual(ledger.balance(db, "venue-b", "flour"), 8)


if __name__ == "__main__":
    unittest.main()
