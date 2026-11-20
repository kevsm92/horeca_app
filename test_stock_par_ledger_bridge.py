"""Synthetic SQLite regression tests for read-only par suggestions."""
import sqlite3
import unittest
from prototypes.inventory.inventory_ledger import initialize, add_ingredient, post_event, balance
from stock_par_ledger_bridge import suggest_from_ledger


class LedgerParBridgeTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:', isolation_level=None)
        initialize(self.db)
        for venue in ('alpha', 'beta'):
            add_ingredient(self.db, venue, 'milk', 'Synthetic milk', 'ml')
        post_event(self.db, 'alpha', 'milk', 'receipt1', 7, 'receipt')
        post_event(self.db, 'beta', 'milk', 'receipt1', 50, 'receipt')

    def tearDown(self):
        self.db.close()

    def test_reservations_and_incoming(self):
        self.assertEqual(suggest_from_ledger(self.db, venue_id='alpha', ingredient_id='milk',
            par_milliunits=12000, reserved_milliunits=2000, incoming_milliunits=1000), 6000)

    def test_tenant_isolation_and_unknown_ingredient(self):
        self.assertEqual(suggest_from_ledger(self.db, venue_id='beta', ingredient_id='milk',
            par_milliunits=12000), 0)
        with self.assertRaises(ValueError):
            suggest_from_ledger(self.db, venue_id='alpha', ingredient_id='missing', par_milliunits=1)

    def test_invalid_reservation_does_not_write(self):
        before = self.db.execute('SELECT COUNT(*) FROM stock_events').fetchone()[0]
        with self.assertRaises(ValueError):
            suggest_from_ledger(self.db, venue_id='alpha', ingredient_id='milk',
                par_milliunits=1000, reserved_milliunits=7001)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM stock_events').fetchone()[0], before)
        self.assertEqual(balance(self.db, 'alpha', 'milk'), 7)

    def test_bool_and_negative_par_rejected(self):
        for par in (True, -1, 1.5):
            with self.assertRaises(ValueError):
                suggest_from_ledger(self.db, venue_id='alpha', ingredient_id='milk', par_milliunits=par)


if __name__ == '__main__':
    unittest.main()
