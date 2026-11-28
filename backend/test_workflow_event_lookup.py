import sqlite3
import unittest
from workflow_outbox import initialize, produce
from workflow_event_lookup import lookup_event

class LookupTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        initialize(self.db)
        self.event_id, _ = produce(self.db,venue_id='synthetic-a',
            event_type='operational.check_due.v1',aggregate_id='synthetic-check',
            aggregate_revision=1,
            payload={'check_id':'synthetic-check','sop_revision_id':'synthetic-r1'},
            mutate=lambda db: None)

    def test_scoped_metadata_without_secrets(self):
        result = lookup_event(self.db,venue_id='synthetic-a',event_id=self.event_id)
        self.assertEqual(result['state'],'pending')
        self.assertEqual(result['attempt_count'],0)
        self.assertEqual(result['event_id'],self.event_id)
        self.assertNotIn('payload_json',result)
        self.assertNotIn('lease_token',result)
        self.assertNotIn('venue_id',result)

    def test_cross_venue_and_unknown_are_indistinguishable(self):
        self.assertIsNone(lookup_event(self.db,venue_id='synthetic-b',event_id=self.event_id))
        self.assertIsNone(lookup_event(self.db,venue_id='synthetic-a',event_id='unknown'))

    def test_invalid_identity(self):
        for venue,event in (('',self.event_id),('synthetic-a',''),(None,self.event_id)):
            with self.assertRaises(ValueError):
                lookup_event(self.db,venue_id=venue,event_id=event)

if __name__ == '__main__': unittest.main()
