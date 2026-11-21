"""Synthetic regression coverage for venue-scoped mock notification keyset paging."""
import sqlite3
import unittest
from reservation_notification_paging import page_mock_intents

class PagingTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.execute('CREATE TABLE reservation_notification_intents (venue_id TEXT,event_id TEXT,kind TEXT,reservation_id TEXT,payload_json TEXT,state TEXT)')
        for venue, event in [('a','e1'),('b','e2'),('a','e2'),('a','e3')]:
            self.db.execute('INSERT INTO reservation_notification_intents VALUES (?,?,?,?,?,?)',
                            (venue,event,'waitlist_offer','synthetic','{"scheduled_utc":"2026-11-16T08:00:00+00:00"}','mock_pending'))
    def tearDown(self): self.db.close()
    def test_cursor_and_isolation(self):
        first,cursor=page_mock_intents(self.db,venue_id='a',limit=2)
        second,last=page_mock_intents(self.db,venue_id='a',after_event_id=cursor,limit=2)
        self.assertEqual([r['event_id'] for r in first+second],['e1','e2','e3'])
        self.assertEqual(cursor,'e2')
        self.assertIsNone(last)
        self.assertEqual([r['event_id'] for r in page_mock_intents(self.db,venue_id='b')[0]],['e2'])
    def test_invalid_inputs(self):
        for kwargs in ({'venue_id':''},{'venue_id':'a','limit':True},{'venue_id':'a','limit':101},
                       {'venue_id':'a','after_event_id':''},{'venue_id':'a','after_event_id':2}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError): page_mock_intents(self.db,**kwargs)
    def test_read_only_and_sql_parameters(self):
        before=self.db.total_changes
        records,cursor=page_mock_intents(self.db,venue_id="a' OR 1=1 --")
        self.assertEqual((records,cursor),([],None))
        self.assertEqual(self.db.total_changes,before)
if __name__=='__main__': unittest.main()
