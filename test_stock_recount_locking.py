"""Synthetic two-connection SQLite recount concurrency regression."""
import os
import sqlite3
import tempfile
import threading
import unittest
from stock_recount_events import initialize, record_event, list_events

BASE = dict(venue_id='venue-fictional', sku_id='sku-fictional', recount_id='recount-1',
            event_type='count_recorded', actor_id='fictional-actor', ledger_revision=1,
            quantity_milli=2000, occurred_at='2026-11-20T23:00:00+01:00')

class LockingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, 'counts.sqlite')
        c = sqlite3.connect(self.path)
        initialize(c)
        c.close()

    def tearDown(self):
        self.tmp.cleanup()

    def connect(self):
        return sqlite3.connect(self.path, timeout=3)

    def test_competing_scopes_cannot_bind_same_recount(self):
        first_locked = threading.Event()
        release_first = threading.Event()
        outcomes = []
        def writer_one():
            c = self.connect()
            c.execute('BEGIN IMMEDIATE')
            c.execute("INSERT INTO stock_recount_events VALUES (?,?,?,?,?,?,?,?,?)",
                      ('e1', BASE['venue_id'], BASE['sku_id'], BASE['recount_id'],
                       BASE['event_type'], BASE['actor_id'], 1, 2000, BASE['occurred_at']))
            first_locked.set()
            release_first.wait(3)
            c.commit()
            c.close()
        def writer_two():
            c = self.connect()
            try:
                record_event(c, event_id='e2', **(BASE | {'venue_id':'other-venue',
                             'event_type':'recount_recorded'}))
                outcomes.append('unexpected_success')
            except ValueError as exc:
                outcomes.append(str(exc))
            finally:
                c.close()
        a = threading.Thread(target=writer_one)
        b = threading.Thread(target=writer_two)
        a.start()
        self.assertTrue(first_locked.wait(3))
        b.start()
        release_first.set()
        a.join(4)
        b.join(4)
        self.assertFalse(a.is_alive() or b.is_alive())
        self.assertEqual(outcomes, ['recount identity bound to another scope'])
        c = self.connect()
        self.assertEqual(len(list_events(c, venue_id=BASE['venue_id'],
                         sku_id=BASE['sku_id'], recount_id=BASE['recount_id'])), 1)
        c.close()

    def test_existing_transaction_rejected_without_commit(self):
        c = self.connect()
        c.execute('BEGIN')
        with self.assertRaisesRegex(ValueError, 'idle SQLite'):
            record_event(c, event_id='e1', **BASE)
        self.assertTrue(c.in_transaction)
        c.rollback()
        c.close()

    def test_duplicate_rollback_leaves_connection_usable(self):
        c = self.connect()
        record_event(c, event_id='e1', **BASE)
        with self.assertRaises(sqlite3.IntegrityError):
            record_event(c, event_id='e1', **BASE)
        self.assertFalse(c.in_transaction)
        record_event(c, event_id='e2', **(BASE | {'event_type':'recount_recorded'}))
        c.close()

if __name__ == '__main__':
    unittest.main()
