"""Offline consumer: turn task.requested outbox events into fictional venue tasks."""
import json
import sqlite3
import unittest
from workflow_outbox import install, enqueue, pending, mock_attempt

def install_tasks(db):
    db.execute("""CREATE TABLE IF NOT EXISTS mock_tasks (
        venue_id TEXT NOT NULL, source_event_id INTEGER NOT NULL,
        title TEXT NOT NULL CHECK(length(title) BETWEEN 1 AND 120),
        PRIMARY KEY (venue_id,source_event_id))""")

def consume_one(db, venue):
    """Process one pending event atomically. Unknown types remain pending for routing."""
    if not isinstance(venue,str) or not venue.strip():
        raise ValueError('venue required')
    with db:
        row=db.execute("""SELECT id,payload FROM workflow_outbox
                          WHERE venue_id=? AND event_type='task.requested'
                          AND state='pending' ORDER BY id LIMIT 1""",(venue,)).fetchone()
        if row is None:
            return False
        event_id, raw=row
        payload=json.loads(raw)
        title=payload.get('title') if isinstance(payload,dict) else None
        if not isinstance(title,str) or not 1 <= len(title.strip()) <= 120:
            mock_attempt(db,venue,event_id,False)
            return False
        db.execute("""INSERT OR IGNORE INTO mock_tasks(venue_id,source_event_id,title)
                      VALUES(?,?,?)""",(venue,event_id,title.strip()))
        if not mock_attempt(db,venue,event_id,True):
            raise RuntimeError('outbox state changed')
        return True

class Tests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(':memory:')
        install(self.db)
        install_tasks(self.db)
    def test_task_created_once_and_isolated(self):
        enqueue(self.db,'a','event-1','task.requested',{'title':'Synthetic fridge check'})
        enqueue(self.db,'b','event-1','task.requested',{'title':'Synthetic bar check'})
        self.assertTrue(consume_one(self.db,'a'))
        self.assertFalse(consume_one(self.db,'a'))
        self.assertEqual(self.db.execute('SELECT title FROM mock_tasks WHERE venue_id=?',('a',)).fetchall(),[('Synthetic fridge check',)])
        self.assertEqual(len(pending(self.db,'b')),1)
    def test_invalid_payload_remains_pending(self):
        enqueue(self.db,'a','bad','task.requested',{'title':''})
        self.assertFalse(consume_one(self.db,'a'))
        self.assertEqual(len(pending(self.db,'a')),1)
        self.assertEqual(self.db.execute('SELECT count(*) FROM mock_tasks').fetchone()[0],0)
    def test_unrelated_event_not_consumed(self):
        enqueue(self.db,'a','other','audit.logged',{})
        self.assertFalse(consume_one(self.db,'a'))
        self.assertEqual(len(pending(self.db,'a')),1)

if __name__=='__main__':
    unittest.main()
