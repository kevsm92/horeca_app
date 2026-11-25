import sqlite3
import unittest
from workflow_outbox import initialize, produce

ARGS = dict(venue_id='synthetic-a', event_type='operational.check_due.v1',
            aggregate_id='synthetic-check-1', aggregate_revision=1,
            payload={'check_id':'synthetic-check-1', 'sop_revision_id':'synthetic-r1'})

class OutboxTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        initialize(self.db)
        self.db.execute('CREATE TABLE domain(id TEXT PRIMARY KEY)')
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_atomic_success_and_duplicate_no_mutation(self):
        eid, fresh = produce(self.db, **ARGS, mutate=lambda db: db.execute("INSERT INTO domain VALUES ('one')"))
        same, again = produce(self.db, **ARGS, mutate=lambda db: self.fail('duplicate mutated domain'))
        self.assertEqual((same, again), (eid, False))
        self.assertTrue(fresh)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM workflow_outbox').fetchone()[0], 1)

    def test_rollback_domain_and_outbox(self):
        def broken(db):
            db.execute("INSERT INTO domain VALUES ('one')")
            raise RuntimeError('synthetic failure')
        with self.assertRaises(RuntimeError):
            produce(self.db, **ARGS, mutate=broken)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM domain').fetchone()[0], 0)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM workflow_outbox').fetchone()[0], 0)

    def test_venue_isolation(self):
        for venue in ('synthetic-a', 'synthetic-b'):
            produce(self.db, **(ARGS | {'venue_id':venue}), mutate=lambda db: None)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM workflow_outbox').fetchone()[0], 2)

    def test_reject_unsafe_payload(self):
        with self.assertRaises(ValueError):
            produce(self.db, **(ARGS | {'payload':{'employee_health':'private'}}), mutate=lambda db: None)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM workflow_outbox').fetchone()[0], 0)

    def test_existing_transaction_rejected(self):
        self.db.execute("INSERT INTO domain VALUES ('pending')")
        with self.assertRaises(ValueError):
            produce(self.db, **ARGS, mutate=lambda db: None)
        self.db.rollback()

if __name__ == '__main__':
    unittest.main()
