"""Offline SQLite transactional outbox claim primitive; no network delivery."""
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS workflow_outbox (
  id INTEGER PRIMARY KEY,
  venue_id TEXT NOT NULL CHECK(length(venue_id)>0),
  event_type TEXT NOT NULL CHECK(length(event_type)>0),
  payload_json TEXT NOT NULL CHECK(json_valid(payload_json)),
  status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','leased','done')),
  attempts INTEGER NOT NULL DEFAULT 0 CHECK(attempts>=0),
  available_at INTEGER NOT NULL DEFAULT 0,
  lease_until INTEGER,
  UNIQUE(venue_id,event_type,id)
);
CREATE INDEX IF NOT EXISTS workflow_outbox_ready ON workflow_outbox(status,available_at,id);
"""

def init(conn):
    conn.executescript(SCHEMA)

def enqueue(conn, venue_id, event_type, payload_json):
    """Call within the caller's transaction alongside its domain write."""
    return conn.execute('INSERT INTO workflow_outbox(venue_id,event_type,payload_json) VALUES (?,?,?)',
                        (venue_id,event_type,payload_json)).lastrowid

def claim(conn, now, lease_seconds=30):
    """Atomically claim one ready event; return (id, venue_id, event_type, payload, attempts)."""
    if lease_seconds <= 0:
        raise ValueError('lease_seconds must be positive')
    with conn:
        row = conn.execute("""UPDATE workflow_outbox
          SET status='leased', lease_until=?, attempts=attempts+1
          WHERE id=(SELECT id FROM workflow_outbox
            WHERE (status='pending' AND available_at<=?) OR
                  (status='leased' AND lease_until<=?)
            ORDER BY id LIMIT 1)
          RETURNING id,venue_id,event_type,payload_json,attempts""",
          (now+lease_seconds,now,now)).fetchone()
    return row

def complete(conn, event_id, attempts):
    """Fencing token prevents stale workers acknowledging a reclaimed event."""
    with conn:
        return conn.execute("""UPDATE workflow_outbox SET status='done',lease_until=NULL
          WHERE id=? AND status='leased' AND attempts=?""",(event_id,attempts)).rowcount == 1

def retry(conn, event_id, attempts, available_at):
    with conn:
        return conn.execute("""UPDATE workflow_outbox SET status='pending',lease_until=NULL,available_at=?
          WHERE id=? AND status='leased' AND attempts=?""",(available_at,event_id,attempts)).rowcount == 1
