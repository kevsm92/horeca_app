"""Synthetic SQLite concurrency regression for order-stock event replay."""
import os
import sqlite3
import tempfile
import threading
import unittest
from order_stock_event import initialize, record_order_consumption


class ConcurrentOrderStockTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.temp.name, 'stock.sqlite')
        db = sqlite3.connect(self.path)
        initialize(db)
        db.close()

    def tearDown(self):
        self.temp.cleanup()

    def race(self, different=False):
        gate = threading.Barrier(2)
        results = [None, None]

        def worker(index):
            db = sqlite3.connect(self.path, timeout=5)
            try:
                gate.wait(timeout=5)
                results[index] = record_order_consumption(
                    db, venue_id='venue-a', event_id='event-1', order_id='order-1',
                    ingredients={'salt': 10 + (index if different else 0)})
            except Exception as exc:
                results[index] = exc
            finally:
                db.close()

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=8)
        self.assertTrue(all(not thread.is_alive() for thread in threads))
        db = sqlite3.connect(self.path)
        try:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM order_stock_events').fetchone()[0], 1)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM order_stock_ledger').fetchone()[0], 1)
        finally:
            db.close()
        return results

    def test_concurrent_identical_retries(self):
        self.assertCountEqual(self.race(), [True, False])

    def test_concurrent_conflicting_retries(self):
        results = self.race(different=True)
        self.assertEqual(sum(value is True for value in results), 1)
        self.assertEqual(sum(isinstance(value, ValueError) for value in results), 1)

    def test_reject_outer_transaction_without_modifying_it(self):
        db = sqlite3.connect(self.path)
        try:
            db.execute('BEGIN')
            with self.assertRaisesRegex(ValueError, 'transaction already active'):
                record_order_consumption(db, venue_id='venue-a', event_id='e',
                                         order_id='o', ingredients={'salt': 1})
            self.assertTrue(db.in_transaction)
            db.rollback()
        finally:
            db.close()


if __name__ == '__main__':
    unittest.main()
