"""Offline venue-scoped task prototype; synthetic data only. Run: python -m unittest horeca_tasks.py"""
import sqlite3
import unittest
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
 venue TEXT NOT NULL, id TEXT NOT NULL, title TEXT NOT NULL,
 assignee TEXT, priority TEXT NOT NULL CHECK(priority IN ('low','normal','high')),
 due_at TEXT, status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open','done')),
 PRIMARY KEY(venue,id));
CREATE TABLE IF NOT EXISTS task_audit (
 seq INTEGER PRIMARY KEY, venue TEXT NOT NULL, task_id TEXT NOT NULL,
 actor TEXT NOT NULL, action TEXT NOT NULL, timestamp TEXT NOT NULL,
 FOREIGN KEY(venue,task_id) REFERENCES tasks(venue,id));
CREATE TRIGGER IF NOT EXISTS audit_immutable_update BEFORE UPDATE ON task_audit
 BEGIN SELECT RAISE(ABORT,'immutable audit'); END;
CREATE TRIGGER IF NOT EXISTS audit_immutable_delete BEFORE DELETE ON task_audit
 BEGIN SELECT RAISE(ABORT,'immutable audit'); END;
"""

def initialize(db):
    db.execute('PRAGMA foreign_keys=ON')
    db.executescript(SCHEMA)

def create(db, venue, task_id, title, actor, assignee=None, priority='normal', due_at=None):
    if not all(isinstance(v,str) and v.strip() for v in (venue,task_id,title,actor)):
        raise ValueError('required identity/title missing')
    with db:
        db.execute('INSERT INTO tasks(venue,id,title,assignee,priority,due_at) VALUES(?,?,?,?,?,?)',
                   (venue,task_id,title,assignee,priority,due_at))
        db.execute('INSERT INTO task_audit(venue,task_id,actor,action,timestamp) VALUES(?,?,?,?,?)',
                   (venue,task_id,actor,'created',datetime.now(timezone.utc).isoformat()))

def complete(db, venue, task_id, actor):
    if not all(isinstance(v,str) and v.strip() for v in (venue,task_id,actor)):
        raise ValueError('required identity missing')
    with db:
        changed = db.execute("UPDATE tasks SET status='done' WHERE venue=? AND id=? AND status='open'",
                             (venue,task_id)).rowcount
        if changed:
            db.execute('INSERT INTO task_audit(venue,task_id,actor,action,timestamp) VALUES(?,?,?,?,?)',
                       (venue,task_id,actor,'completed',datetime.now(timezone.utc).isoformat()))
    return bool(changed)

def list_for_venue(db, venue):
    return db.execute('SELECT id,title,assignee,priority,due_at,status FROM tasks WHERE venue=? ORDER BY id',
                      (venue,)).fetchall()

class TaskTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(':memory:')
        initialize(self.db)
        create(self.db,'fictional-a','t1','Check fictional fridge','demo-manager')
    def tearDown(self):
        self.db.close()
    def test_isolation(self):
        self.assertEqual(list_for_venue(self.db,'fictional-b'),[])
        self.assertFalse(complete(self.db,'fictional-b','t1','demo-manager'))
        self.assertEqual(list_for_venue(self.db,'fictional-a')[0][-1],'open')
    def test_idempotent_completion(self):
        self.assertTrue(complete(self.db,'fictional-a','t1','demo-manager'))
        self.assertFalse(complete(self.db,'fictional-a','t1','demo-manager'))
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM task_audit').fetchone()[0],2)
    def test_immutable_audit(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute('DELETE FROM task_audit')
    def test_duplicate(self):
        with self.assertRaises(sqlite3.IntegrityError):
            create(self.db,'fictional-a','t1','Duplicate','demo-manager')

if __name__ == '__main__':
    unittest.main()
