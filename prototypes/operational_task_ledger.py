"""Offline venue-scoped operational task ledger; synthetic use only."""
import sqlite3
from datetime import datetime, timezone

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS tasks (
 venue_id TEXT NOT NULL, task_id TEXT NOT NULL, title TEXT NOT NULL,
 assignee TEXT NOT NULL, priority TEXT NOT NULL CHECK(priority IN ('low','normal','high')),
 due_at TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'open'
 CHECK(status IN ('open','completed')), revision INTEGER NOT NULL DEFAULT 0,
 PRIMARY KEY(venue_id,task_id));
CREATE TABLE IF NOT EXISTS task_events (
 event_id INTEGER PRIMARY KEY AUTOINCREMENT, venue_id TEXT NOT NULL,
 task_id TEXT NOT NULL, actor TEXT NOT NULL, kind TEXT NOT NULL,
 occurred_at TEXT NOT NULL, FOREIGN KEY(venue_id,task_id)
 REFERENCES tasks(venue_id,task_id));
CREATE TRIGGER IF NOT EXISTS no_event_update BEFORE UPDATE ON task_events
 BEGIN SELECT RAISE(ABORT,'immutable audit'); END;
CREATE TRIGGER IF NOT EXISTS no_event_delete BEFORE DELETE ON task_events
 BEGIN SELECT RAISE(ABORT,'immutable audit'); END;
"""

def utc_now():
    return datetime.now(timezone.utc).isoformat()

class TaskLedger:
    def __init__(self, db):
        self.db = db
        self.db.executescript(SCHEMA)

    def create(self, *, venue, task, title, assignee, priority, due_at, actor):
        if not all((venue, task, title, assignee, actor)):
            raise ValueError('missing required identity')
        stamp = datetime.fromisoformat(due_at.replace('Z', '+00:00'))
        if stamp.tzinfo is None:
            raise ValueError('due date requires timezone')
        with self.db:
            self.db.execute('INSERT INTO tasks(venue_id,task_id,title,assignee,priority,due_at) VALUES(?,?,?,?,?,?)',
                            (venue,task,title,assignee,priority,due_at))
            self._event(venue,task,actor,'created')

    def complete(self, *, venue, task, actor, expected_revision):
        if not all((venue,task,actor)) or expected_revision < 0:
            raise ValueError('invalid completion request')
        with self.db:
            row = self.db.execute('UPDATE tasks SET status=\'completed\',revision=revision+1 '
                                  'WHERE venue_id=? AND task_id=? AND assignee=? '
                                  'AND status=\'open\' AND revision=? RETURNING revision',
                                  (venue,task,actor,expected_revision)).fetchone()
            if row is None:
                raise PermissionError('not assigned, wrong venue, or stale completion')
            self._event(venue,task,actor,'completed')
            return row[0]

    def history(self, *, venue, task, actor):
        row = self.db.execute('SELECT assignee FROM tasks WHERE venue_id=? AND task_id=?',
                              (venue,task)).fetchone()
        if row is None or row[0] != actor:
            raise PermissionError('task history access denied')
        return self.db.execute('SELECT kind,actor,occurred_at FROM task_events '
                               'WHERE venue_id=? AND task_id=? ORDER BY event_id',
                               (venue,task)).fetchall()

    def _event(self, venue, task, actor, kind):
        self.db.execute('INSERT INTO task_events(venue_id,task_id,actor,kind,occurred_at) '
                        'VALUES(?,?,?,?,?)',(venue,task,actor,kind,utc_now()))
