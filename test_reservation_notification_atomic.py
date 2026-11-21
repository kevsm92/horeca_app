"""Synthetic tests for atomic mock reservation intents."""
import sqlite3
import unittest
from reservation_notification_mock import initialize, enqueue_mock_in_transaction, enqueue_mock

ARGS = dict(venue_id='fictional-venue',event_id='event-1',kind='waitlist_offer',reservation_id='reservation-1',payload={'scheduled_utc':'2026-11-16T12:00:00+00:00'})

class AtomicIntentTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:', isolation_level=None)
        initialize(self.db)
        self.db.execute('CREATE TABLE trusted_events(venue_id TEXT, event_id TEXT, PRIMARY KEY(venue_id,event_id))')
    def tearDown(self):
        self.db.close()
    def test_requires_transaction(self):
        with self.assertRaisesRegex(ValueError, 'active transaction'):
            enqueue_mock_in_transaction(self.db, **ARGS)
    def test_commit_with_source_event(self):
        self.db.execute('BEGIN IMMEDIATE')
        self.db.execute('INSERT INTO trusted_events VALUES (?,?)',(ARGS['venue_id'],ARGS['event_id']))
        self.assertTrue(enqueue_mock_in_transaction(self.db, **ARGS))
        self.assertTrue(self.db.in_transaction)
        self.db.commit()
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM reservation_notification_intents').fetchone()[0],1)
    def test_rollback_both(self):
        self.db.execute('BEGIN IMMEDIATE')
        self.db.execute('INSERT INTO trusted_events VALUES (?,?)',(ARGS['venue_id'],ARGS['event_id']))
        enqueue_mock_in_transaction(self.db, **ARGS)
        self.db.rollback()
        for table in ('trusted_events','reservation_notification_intents'):
            self.assertEqual(self.db.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0],0)
    def test_replay_and_conflict_do_not_commit(self):
        self.db.execute('BEGIN IMMEDIATE')
        self.assertTrue(enqueue_mock_in_transaction(self.db, **ARGS))
        self.assertFalse(enqueue_mock_in_transaction(self.db, **ARGS))
        with self.assertRaisesRegex(ValueError,'event id conflict'):
            enqueue_mock_in_transaction(self.db, **{**ARGS,'reservation_id':'other'})
        self.assertTrue(self.db.in_transaction)
        self.db.rollback()
    def test_venue_scoping_and_no_delivery(self):
        self.db.execute('BEGIN IMMEDIATE')
        enqueue_mock_in_transaction(self.db, **ARGS)
        enqueue_mock_in_transaction(self.db, **{**ARGS,'venue_id':'other-venue'})
        self.db.commit()
        self.assertEqual(self.db.execute('SELECT DISTINCT state FROM reservation_notification_intents').fetchall(),[('mock_pending',)])
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM reservation_notification_intents').fetchone()[0],2)
    def test_standalone_rejects_external_transaction(self):
        self.db.execute('BEGIN IMMEDIATE')
        with self.assertRaisesRegex(ValueError,'existing transaction'):
            enqueue_mock(self.db, **ARGS)
        self.db.rollback()

if __name__ == '__main__': unittest.main()
