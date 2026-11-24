"""Offline venue-scoped task engine; synthetic data only."""
import sqlite3
from datetime import datetime

def _time(value):
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("timezone required")
    return dt.isoformat()

def initialize(db):
    db.execute("PRAGMA foreign_keys=ON")
    db.executescript("""
    CREATE TABLE IF NOT EXISTS tasks(
      venue_id TEXT NOT NULL, task_id TEXT NOT NULL, title TEXT NOT NULL,
      assignee_id TEXT, priority TEXT NOT NULL CHECK(priority IN ('low','normal','high')),
      due_at TEXT, status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open','done')),
      PRIMARY KEY(venue_id,task_id));
    CREATE TABLE IF NOT EXISTS task_events(
      event_id INTEGER PRIMARY KEY, venue_id TEXT NOT NULL, task_id TEXT NOT NULL,
      actor_id TEXT NOT NULL, action TEXT NOT NULL, occurred_at TEXT NOT NULL,
      FOREIGN KEY(venue_id,task_id) REFERENCES tasks(venue_id,task_id));
    CREATE TRIGGER IF NOT EXISTS events_immutable_update BEFORE UPDATE ON task_events
      BEGIN SELECT RAISE(ABORT,'audit immutable'); END;
    CREATE TRIGGER IF NOT EXISTS events_immutable_delete BEFORE DELETE ON task_events
      BEGIN SELECT RAISE(ABORT,'audit immutable'); END;
    """)

def create_task(db, *, venue_id, task_id, title, actor_id, occurred_at,
                assignee_id=None, priority='normal', due_at=None):
    if not all((venue_id, task_id, title.strip(), actor_id)):
        raise ValueError("required fields missing")
    at = _time(occurred_at)
    due = _time(due_at) if due_at else None
    with db:
        db.execute("INSERT INTO tasks(venue_id,task_id,title,assignee_id,priority,due_at) VALUES(?,?,?,?,?,?)",
                   (venue_id,task_id,title,assignee_id,priority,due))
        db.execute("INSERT INTO task_events(venue_id,task_id,actor_id,action,occurred_at) VALUES(?,?,?,?,?)",
                   (venue_id,task_id,actor_id,'created',at))

def complete_task(db, *, venue_id, task_id, actor_id, occurred_at):
    if not all((venue_id,task_id,actor_id)):
        raise ValueError("identity required")
    at = _time(occurred_at)
    with db:
        changed = db.execute("UPDATE tasks SET status='done' WHERE venue_id=? AND task_id=? AND status='open'",
                             (venue_id,task_id)).rowcount
        if changed:
            db.execute("INSERT INTO task_events(venue_id,task_id,actor_id,action,occurred_at) VALUES(?,?,?,?,?)",
                       (venue_id,task_id,actor_id,'completed',at))
    return bool(changed)

def list_tasks(db, *, venue_id):
    if not venue_id:
        raise ValueError("venue required")
    return db.execute("SELECT task_id,title,assignee_id,priority,due_at,status FROM tasks WHERE venue_id=? ORDER BY task_id",
                      (venue_id,)).fetchall()
