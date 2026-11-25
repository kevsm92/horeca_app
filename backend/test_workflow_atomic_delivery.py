import json
import sqlite3
import unittest
from datetime import datetime, timezone, timedelta

from workflow_outbox import initialize as init_outbox
from workflow_task_trigger import initialize as init_tasks
from workflow_atomic_delivery import deliver_check_due


class AtomicDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        init_outbox(self.db)
        init_tasks(self.db)
        self.now = datetime(2026, 11, 25, 12, tzinfo=timezone.utc)
        self.payload = json.dumps({'check_id': 'synthetic-check-1',
                                   'sop_revision_id': 'synthetic-revision-1'},
                                  sort_keys=True, separators=(',', ':'))
        self.event = {'event_id': 'synthetic-event-1',
                      'event_type': 'operational.check_due.v1',
                      'payload_json': self.payload}
        self.db.execute('''INSERT INTO workflow_outbox
            (event_id,venue_id,event_type,event_version,aggregate_id,aggregate_revision,
             payload_json,created_at_utc,available_at_utc,state,lease_token,lease_expires_at_utc)
             VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',
             ('synthetic-event-1','synthetic-a','operational.check_due.v1',1,
              'synthetic-check-1',1,self.payload,self.now.isoformat(),self.now.isoformat(),
              'leased','synthetic-token', (self.now+timedelta(minutes=1)).isoformat()))
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def deliver(self, **kwargs):
        args = dict(venue_id='synthetic-a', event=self.event,
                    lease_token='synthetic-token', now=self.now)
        args.update(kwargs)
        return deliver_check_due(self.db, **args)

    def test_atomic_success(self):
        self.assertTrue(self.deliver())
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM workflow_mock_tasks').fetchone()[0],1)
        self.assertEqual(self.db.execute('SELECT state FROM workflow_outbox').fetchone()[0],'delivered')
        self.assertFalse(self.deliver())

    def test_wrong_venue_token_and_expiry_do_not_project(self):
        for args in ({'venue_id':'synthetic-b'}, {'lease_token':'other'},
                     {'now':self.now+timedelta(minutes=2)}):
            self.assertFalse(self.deliver(**args))
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM workflow_mock_tasks').fetchone()[0],0)

    def test_tampered_payload_rolls_back(self):
        tampered = dict(self.event, payload_json=json.dumps({'check_id':'synthetic-check-2',
                          'sop_revision_id':'synthetic-revision-1'}))
        with self.assertRaises(ValueError):
            self.deliver(event=tampered)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM workflow_mock_tasks').fetchone()[0],0)
        self.assertEqual(self.db.execute('SELECT state FROM workflow_outbox').fetchone()[0],'leased')

    def test_preexisting_projection_is_idempotent(self):
        self.db.execute('''INSERT INTO workflow_mock_tasks
          (venue_id,event_id,check_id,sop_revision_id) VALUES (?,?,?,?)''',
          ('synthetic-a','synthetic-event-1','synthetic-check-1','synthetic-revision-1'))
        self.db.commit()
        self.assertTrue(self.deliver())
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM workflow_mock_tasks').fetchone()[0],1)

    def test_validation_and_transaction_ownership(self):
        with self.assertRaises(ValueError):
            self.deliver(now=datetime(2026,11,25))
        self.db.execute('BEGIN')
        with self.assertRaises(ValueError):
            self.deliver()
        self.db.rollback()


if __name__ == '__main__':
    unittest.main()
