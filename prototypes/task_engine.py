"""Offline venue-scoped task prototype. NOT an authenticated API."""
import sqlite3
from datetime import datetime, timezone

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS tasks (
 venue_id TEXT NOT NULL, task_id TEXT NOT NULL, title TEXT NOT NULL,
 assignee_id TEXT, priority TEXT NOT NULL CHECK(priority IN ('low','normal','high')),
 due_at TEXT, status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open','completed')),
 revision INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(venue_id,task_id));
CREATE TABLE IF NOT EXISTS task_events (
 event_id INTEGER PRIMARY KEY AUTOINCREMENT, venue_id TEXT NOT NULL,
 task_id TEXT NOT NULL, actor_id TEXT NOT NULL, action TEXT NOT NULL,
 occurred_at TEXT NOT NULL,
 FOREIGN KEY(venue_id,task_id) REFERENCES tasks(venue_id,task_id));
CREATE TRIGGER IF NOT EXISTS immutable_task_events_update BEFORE UPDATE ON task_events
 BEGIN SELECT RAISE(ABORT,'immutable evidence'); END;
CREATE TRIGGER IF NOT EXISTS immutable_task_events_delete BEFORE DELETE ON task_events
 BEGIN SELECT RAISE(ABORT,'immutable evidence'); END;
"""

def connect(path=":memory:"):
    db = sqlite3.connect(path, isolation_level=None)
    db.executescript(SCHEMA)
    return db

def create_task(db, *, venue_id, task_id, title, actor_id, priority='normal', assignee_id=None, due_at=None):
    if not all(isinstance(x,str) and x.strip() for x in (venue_id,task_id,title,actor_id)):
        raise ValueError('required identifiers/title')
    if due_at is not None:
        parsed = datetime.fromisoformat(due_at)
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError('due_at requires timezone offset')
    with db:
        db.execute('INSERT INTO tasks(venue_id,task_id,title,assignee_id,priority,due_at) VALUES(?,?,?,?,?,?)',
                   (venue_id,task_id,title,assignee_id,priority,due_at))
        db.execute('INSERT INTO task_events(venue_id,task_id,actor_id,action,occurred_at) VALUES(?,?,?,?,?)',
                   (venue_id,task_id,actor_id,'created',datetime.now(timezone.utc).isoformat()))

def complete_task(db, *, venue_id, task_id, actor_id, expected_revision):
    """Caller MUST derive actor/venue from authenticated authorization, not client input."""
    if not venue_id or not task_id or not actor_id or type(expected_revision) is not int:
        raise ValueError('invalid completion request')
    with db:
        changed = db.execute("UPDATE tasks SET status='completed',revision=revision+1 "
                             "WHERE venue_id=? AND task_id=? AND status='open' AND revision=?",
                             (venue_id,task_id,expected_revision)).rowcount
        if changed != 1:
            raise ValueError('task missing, completed, or stale revision')
        db.execute('INSERT INTO task_events(venue_id,task_id,actor_id,action,occurred_at) VALUES(?,?,?,?,?)',
                   (venue_id,task_id,actor_id,'completed',datetime.now(timezone.utc).isoformat()))

def list_tasks(db, *, venue_id):
    if not venue_id:
        raise ValueError('venue required')
    return db.execute('SELECT task_id,title,assignee_id,priority,due_at,status,revision FROM tasks WHERE venue_id=? ORDER BY task_id',
                      (venue_id,)).fetchall()
