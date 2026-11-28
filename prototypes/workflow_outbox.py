"""Venue-scoped offline SQLite outbox. Caller owns the domain transaction."""
import json
import sqlite3
import unittest
from datetime import datetime, timezone

def install(db):
    db.execute("""CREATE TABLE IF NOT EXISTS workflow_outbox (
      id INTEGER PRIMARY KEY, venue_id TEXT NOT NULL, event_key TEXT NOT NULL,
      event_type TEXT NOT NULL, payload TEXT NOT NULL,
      state TEXT NOT NULL DEFAULT 'pending' CHECK(state IN ('pending','delivered')),
      attempts INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL,
      UNIQUE(venue_id,event_key))""")

def enqueue(db, venue, key, kind, payload):
    if not all(isinstance(v,str) and v.strip() for v in (venue,key,kind)):
        raise ValueError("venue/key/kind required")
    if not isinstance(payload,dict):
        raise ValueError("payload must be object")
    data=json.dumps(payload,sort_keys=True,allow_nan=False)
    existing=db.execute("SELECT id,event_type,payload FROM workflow_outbox WHERE venue_id=? AND event_key=?",(venue,key)).fetchone()
    if existing:
        if existing[1:] != (kind,data):
            raise ValueError("conflicting replay")
        return existing[0]
    return db.execute("INSERT INTO workflow_outbox (venue_id,event_key,event_type,payload,created_at) VALUES (?,?,?,?,?)",
       (venue,key,kind,data,datetime.now(timezone.utc).isoformat())).lastrowid

def pending(db, venue):
    if not isinstance(venue,str) or not venue.strip():
        raise ValueError("venue required")
    return db.execute("SELECT id,event_type,payload,attempts FROM workflow_outbox WHERE venue_id=? AND state='pending' ORDER BY id",(venue,)).fetchall()

def mock_attempt(db, venue, event_id, delivered=False):
    return db.execute("""UPDATE workflow_outbox SET attempts=attempts+1,
      state=CASE WHEN ? THEN 'delivered' ELSE state END
      WHERE venue_id=? AND id=? AND state='pending'""",
      (int(bool(delivered)),venue,event_id)).rowcount==1

class Tests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(':memory:')
        install(self.db)
    def tearDown(self):
        self.db.close()
    def test_isolation_and_replay(self):
        a=enqueue(self.db,'a','key','task.mock',{})
        self.assertEqual(a,enqueue(self.db,'a','key','task.mock',{}))
        self.assertNotEqual(a,enqueue(self.db,'b','key','task.mock',{}))
        self.assertFalse(mock_attempt(self.db,'b',a,True))
        self.assertEqual(len(pending(self.db,'a')),1)
        with self.assertRaises(ValueError):
            enqueue(self.db,'a','key','task.mock',{'changed':True})
    def test_transaction_and_retry(self):
        self.db.execute('BEGIN')
        enqueue(self.db,'a','key','task.mock',{})
        self.db.rollback()
        self.assertEqual(pending(self.db,'a'),[])
        event=enqueue(self.db,'a','key','task.mock',{})
        self.assertTrue(mock_attempt(self.db,'a',event))
        self.assertEqual(pending(self.db,'a')[0][3],1)
        self.assertTrue(mock_attempt(self.db,'a',event,True))
        self.assertFalse(mock_attempt(self.db,'a',event,True))
        self.assertEqual(pending(self.db,'a'),[])
    def test_reject_invalid(self):
        with self.assertRaises(ValueError): enqueue(self.db,'','key','type',{})
        with self.assertRaises(ValueError): enqueue(self.db,'a','key','type',[])

if __name__=='__main__':
    unittest.main()
