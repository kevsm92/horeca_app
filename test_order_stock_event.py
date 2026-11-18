import sqlite3
import unittest
from order_stock_event import initialize, record_order_consumption


class OrderStockEventTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        initialize(self.db)
        self.args = dict(venue_id='venue-demo', event_id='event-1', order_id='order-1',
                         ingredients={'tomato-g': 250000, 'salt-g': 3000})

    def tearDown(self):
        self.db.close()

    def test_atomic_deductions_and_idempotent_replay(self):
        self.assertTrue(record_order_consumption(self.db, **self.args))
        self.assertFalse(record_order_consumption(self.db, **self.args))
        self.assertEqual(self.db.execute('SELECT ingredient_id,delta_milliunits FROM order_stock_ledger ORDER BY ingredient_id').fetchall(),
                         [('salt-g', -3000), ('tomato-g', -250000)])

    def test_reuse_with_changed_payload_rejected_without_new_ledger(self):
        record_order_consumption(self.db, **self.args)
        with self.assertRaisesRegex(ValueError, 'reused'):
            record_order_consumption(self.db, **{**self.args, 'ingredients': {'salt-g': 4}})
        self.assertEqual(self.db.execute('SELECT count(*) FROM order_stock_ledger').fetchone()[0], 2)

    def test_same_event_id_isolated_between_venues(self):
        record_order_consumption(self.db, **self.args)
        self.assertTrue(record_order_consumption(self.db, **{**self.args, 'venue_id': 'other-demo'}))
        self.assertEqual(self.db.execute('SELECT count(*) FROM order_stock_ledger').fetchone()[0], 4)

    def test_invalid_quantities_do_not_write(self):
        for invalid in (0, -1, 1.5, True, '5', 1_000_000_001):
            with self.assertRaises(ValueError):
                record_order_consumption(self.db, **{**self.args, 'ingredients': {'salt-g': invalid}})
        self.assertEqual(self.db.execute('SELECT count(*) FROM order_stock_events').fetchone()[0], 0)

    def test_failed_ledger_insert_rolls_back_event(self):
        self.db.execute("CREATE TRIGGER reject_salt BEFORE INSERT ON order_stock_ledger WHEN NEW.ingredient_id='salt-g' BEGIN SELECT RAISE(ABORT,'synthetic failure'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            record_order_consumption(self.db, **self.args)
        self.assertEqual(self.db.execute('SELECT count(*) FROM order_stock_events').fetchone()[0], 0)
        self.assertEqual(self.db.execute('SELECT count(*) FROM order_stock_ledger').fetchone()[0], 0)


if __name__ == '__main__':
    unittest.main()
