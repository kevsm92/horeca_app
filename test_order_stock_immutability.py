import sqlite3
import unittest
from order_stock_event import initialize, record_order_consumption


class OrderStockImmutabilityTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        initialize(self.db)
        record_order_consumption(self.db, venue_id='venue-a', event_id='event-a',
                                 order_id='order-a', ingredients={'flour': 1200})

    def tearDown(self):
        self.db.close()

    def test_ledger_cannot_be_updated_or_deleted(self):
        for statement in (
            "UPDATE order_stock_ledger SET delta_milliunits=-1 WHERE venue_id='venue-a'",
            "DELETE FROM order_stock_ledger WHERE venue_id='venue-a'",
        ):
            with self.subTest(statement=statement), self.assertRaises(sqlite3.IntegrityError):
                self.db.execute(statement)
        self.assertEqual(self.db.execute('SELECT delta_milliunits FROM order_stock_ledger').fetchone()[0], -1200)

    def test_event_identity_and_payload_cannot_be_rewritten_or_deleted(self):
        for statement in (
            "UPDATE order_stock_events SET payload='{}' WHERE venue_id='venue-a'",
            "DELETE FROM order_stock_events WHERE venue_id='venue-a'",
        ):
            with self.subTest(statement=statement), self.assertRaises(sqlite3.IntegrityError):
                self.db.execute(statement)
        self.assertEqual(self.db.execute('SELECT count(*) FROM order_stock_events').fetchone()[0], 1)

    def test_identical_replay_remains_noop(self):
        self.assertFalse(record_order_consumption(self.db, venue_id='venue-a', event_id='event-a',
                                                  order_id='order-a', ingredients={'flour': 1200}))
        self.assertEqual(self.db.execute('SELECT count(*) FROM order_stock_ledger').fetchone()[0], 1)


if __name__ == '__main__':
    unittest.main()
