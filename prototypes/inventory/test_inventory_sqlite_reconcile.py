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


    def test_reconciliation_closes_its_own_read_transaction(self):
        post_event(self.db, 'north', 'flour', 'r', 5, 'receipt')
        self.assertFalse(self.db.in_transaction)
        self.assertEqual(reconcile_sqlite(self.db, 'north')['flour'], 5)
        self.assertFalse(self.db.in_transaction)

    def test_reconciliation_preserves_caller_transaction(self):
        post_event(self.db, 'north', 'flour', 'r', 5, 'receipt')
        self.db.execute('BEGIN')
        try:
            self.assertEqual(reconcile_sqlite(self.db, 'north')['flour'], 5)
            self.assertTrue(self.db.in_transaction)
        finally:
            self.db.rollback()

    def test_failed_reconciliation_releases_owned_transaction(self):
        self.db.execute("DROP TRIGGER stock_no_update")
        self.db.execute("DROP TRIGGER stock_no_delete")
        self.db.execute(
            "INSERT INTO stock_events(venue_id,event_id,ingredient_id,delta,reason) "
            "VALUES(?,?,?,?,?)", ('north', 'bad', 'flour', -1, 'use')
        )
        with self.assertRaises(ValueError):
            reconcile_sqlite(self.db, 'north')
        self.assertFalse(self.db.in_transaction)


    def test_wal_writer_does_not_change_reconciliation_snapshot(self):
        """A second connection commits between reader queries; reader stays consistent."""
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            filename = os.path.join(directory, 'inventory.sqlite3')
            reader = sqlite3.connect(filename, isolation_level=None)
            writer = sqlite3.connect(filename, isolation_level=None)
            try:
                reader.execute('PRAGMA journal_mode=WAL')
                initialize(reader)
                add_ingredient(reader, 'north', 'flour', 'Flour', 'g')
                post_event(reader, 'north', 'flour', 'initial', 10, 'receipt')
                triggered = []
                def on_query(sql):
                    if ('FROM stock_events' in sql and not triggered):
                        triggered.append(True)
                        post_event(writer, 'north', 'flour', 'concurrent', 7, 'receipt')
                reader.set_trace_callback(on_query)
                self.assertEqual(reconcile_sqlite(reader, 'north'), {'flour': 10})
                reader.set_trace_callback(None)
                self.assertEqual(len(triggered), 1)
                self.assertFalse(reader.in_transaction)
                self.assertEqual(reconcile_sqlite(reader, 'north'), {'flour': 17})
            finally:
                reader.set_trace_callback(None)
                writer.close()
                reader.close()


if __name__ == '__main__':
    unittest.main()
