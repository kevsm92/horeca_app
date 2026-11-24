"""Offline venue-scoped task engine; caller must authenticate and authorize actors."""
import sqlite3
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
 venue_id TEXT NOT NULL, id TEXT NOT NULL, title TEXT NOT NULL,
 assignee_id TEXT, priority TEXT NOT NULL CHECK(priority IN ('low','normal','high')),
 due_at TEXT, status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open','completed')),
 completed_at TEXT, PRIMARY KEY(venue_id,id),
 CHECK(length(trim(title))>0),
 CHECK((status='open' AND completed_at IS NULL) OR (status='completed' AND completed_at IS NOT NULL))
);
CREATE TABLE IF NOT EXISTS task_events (
 event_id INTEGER PRIMARY KEY AUTOINCREMENT, venue_id TEXT NOT NULL, task_id TEXT NOT NULL,
 actor_id TEXT NOT NULL, action TEXT NOT NULL CHECK(action IN ('created','completed')),
 occurred_at TEXT NOT NULL,
 FOREIGN KEY(venue_id,task_id) REFERENCES tasks(venue_id,id)
);
CREATE TRIGGER IF NOT EXISTS immutable_task_events_update BEFORE UPDATE ON task_events BEGIN SELECT RAISE(ABORT,'audit immutable'); END;
CREATE TRIGGER IF NOT EXISTS immutable_task_events_delete BEFORE DELETE ON task_events BEGIN SELECT RAISE(ABORT,'audit immutable'); END;
"""

def initialize(db):
    db.execute('PRAGMA foreign_keys=ON')
    db.executescript(SCHEMA)

def _now():
    return datetime.now(timezone.utc).isoformat()

def create_task(db, *, venue_id, task_id, title, actor_id, assignee_id=None, priority='normal', due_at=None):
    if not all(isinstance(x,str) and x.strip() for x in (venue_id,task_id,title,actor_id)):
        raise ValueError('required fields')
    with db:
        db.execute('INSERT INTO tasks(venue_id,id,title,assignee_id,priority,due_at) VALUES (?,?,?,?,?,?)',
                   (venue_id,task_id,title,assignee_id,priority,due_at))
        db.execute('INSERT INTO task_events(venue_id,task_id,actor_id,action,occurred_at) VALUES (?,?,?,?,?)',
                   (venue_id,task_id,actor_id,'created',_now()))

def complete_task(db, *, venue_id, task_id, actor_id):
    if not all(isinstance(x,str) and x.strip() for x in (venue_id,task_id,actor_id)):
        raise ValueError('required fields')
    with db:
        result=db.execute("UPDATE tasks SET status='completed',completed_at=? WHERE venue_id=? AND id=? AND status='open'",
                          (_now(),venue_id,task_id))
        if result.rowcount != 1:
            raise ValueError('task not open in venue')
        db.execute('INSERT INTO task_events(venue_id,task_id,actor_id,action,occurred_at) VALUES (?,?,?,?,?)',
                   (venue_id,task_id,actor_id,'completed',_now()))

def list_tasks(db, *, venue_id):
    if not isinstance(venue_id,str) or not venue_id.strip():
        raise ValueError('venue required')
    return db.execute('SELECT id,title,assignee_id,priority,due_at,status,completed_at FROM tasks WHERE venue_id=? ORDER BY id', (venue_id,)).fetchall()
