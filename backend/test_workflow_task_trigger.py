import json
import sqlite3
import unittest
from workflow_task_trigger import initialize, project_check_due

class TriggerTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.execute("""CREATE TABLE workflow_outbox (
            event_id TEXT PRIMARY KEY, venue_id TEXT NOT NULL, event_type TEXT NOT NULL,
            payload_json TEXT NOT NULL, state TEXT NOT NULL)""")
        initialize(self.db)
        self.eid = 'synthetic-event-1'
        payload = {'check_id':'synthetic-check-1','sop_revision_id':'synthetic-r1'}
        self.event = dict(event_id=self.eid, event_type='operational.check_due.v1',
                          payload_json=json.dumps(payload,sort_keys=True,separators=(',',':')))
        self.db.execute('INSERT INTO workflow_outbox VALUES (?,?,?,?,?)',
                        (self.eid,'synthetic-a',self.event['event_type'],self.event['payload_json'],'leased'))
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_idempotent_projection(self):
        self.assertTrue(project_check_due(self.db,venue_id='synthetic-a',event=self.event))
        self.assertFalse(project_check_due(self.db,venue_id='synthetic-a',event=self.event))
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM workflow_mock_tasks').fetchone()[0],1)
        self.assertEqual(self.db.execute('SELECT state FROM workflow_outbox').fetchone()[0],'leased')

    def test_wrong_venue_rejected(self):
        with self.assertRaises(ValueError):
            project_check_due(self.db,venue_id='synthetic-b',event=self.event)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM workflow_mock_tasks').fetchone()[0],0)

    def test_tampered_payload_rejected(self):
        event = self.event | {'payload_json':json.dumps({'check_id':'synthetic-other','sop_revision_id':'synthetic-r1'})}
        with self.assertRaises(ValueError):
            project_check_due(self.db,venue_id='synthetic-a',event=event)

    def test_unsupported_event_rejected(self):
        with self.assertRaises(ValueError):
            project_check_due(self.db,venue_id='synthetic-a',event=self.event | {'event_type':'payments.charge'})

if __name__=='__main__': unittest.main()
