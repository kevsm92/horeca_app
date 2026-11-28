import sqlite3
import unittest
from datetime import datetime, timezone
from workflow_outbox import initialize, enqueue, dispatch_mock
from workflow_dead_letter import requeue_dead

NOW = datetime(2026, 11, 25, 7, tzinfo=timezone.utc)

class DeadLetterTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        initialize(self.db)
        enqueue(self.db, 'venue-a', 'task-1', 'task.created', {'synthetic': True}, NOW)
        enqueue(self.db, 'venue-b', 'task-1', 'task.created', {}, NOW)
        def fail(*args): raise RuntimeError('mock')
        dispatch_mock(self.db, 'venue-a', NOW, fail, max_attempts=1)

    def test_requeue_preserves_attempts_and_payload(self):
        before = self.db.execute("SELECT attempts,payload FROM workflow_outbox WHERE venue_id='venue-a'").fetchone()
        self.assertTrue(requeue_dead(self.db, 'venue-a', 'task-1', NOW))
        self.assertEqual(self.db.execute("SELECT attempts,payload FROM workflow_outbox WHERE venue_id='venue-a'").fetchone(), before)
        self.assertEqual(dispatch_mock(self.db, 'venue-a', NOW, lambda *args: None), 1)
        self.assertFalse(requeue_dead(self.db, 'venue-a', 'task-1', NOW))

    def test_cross_venue_and_pending_rejected(self):
        self.assertFalse(requeue_dead(self.db, 'venue-b', 'missing', NOW))
        self.assertFalse(requeue_dead(self.db, 'venue-b', 'task-1', NOW))
        self.assertEqual(self.db.execute("SELECT status FROM workflow_outbox WHERE venue_id='venue-b'").fetchone()[0], 'pending')

    def test_validation_and_rollback(self):
        with self.assertRaises(ValueError): requeue_dead(self.db, '', 'task-1', NOW)
        with self.assertRaises(ValueError): requeue_dead(self.db, 'venue-a', 'task-1', datetime(2026,11,25))
        self.db.commit()
        with self.assertRaises(RuntimeError):
            with self.db:
                self.assertTrue(requeue_dead(self.db, 'venue-a', 'task-1', NOW))
                raise RuntimeError('abort')
        self.assertEqual(self.db.execute("SELECT status FROM workflow_outbox WHERE venue_id='venue-a'").fetchone()[0], 'dead')

if __name__ == '__main__': unittest.main()
