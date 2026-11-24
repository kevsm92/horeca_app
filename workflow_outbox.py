"""Offline venue-scoped SQLite transactional outbox; synthetic data only.

Enqueue within the caller's domain transaction. No external delivery.
"""
import json
import sqlite3
from datetime import datetime, timedelta, timezone


def initialize(db: sqlite3.Connection) -> None:
    db.execute("""CREATE TABLE IF NOT EXISTS workflow_outbox (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        venue_id TEXT NOT NULL CHECK(length(venue_id)>0),
        event_key TEXT NOT NULL CHECK(length(event_key)>0),
        event_type TEXT NOT NULL CHECK(length(event_type)>0),
        payload TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','delivered','dead')),
        attempts INTEGER NOT NULL DEFAULT 0 CHECK(attempts>=0),
        next_attempt_at TEXT NOT NULL,
        UNIQUE(venue_id,event_key)
    )""")


def enqueue(db: sqlite3.Connection, venue_id: str, event_key: str,
            event_type: str, payload: dict, now: datetime) -> bool:
    """Insert inside caller-owned transaction; duplicate keys are no-ops."""
    if not all(isinstance(v, str) and v.strip() for v in (venue_id, event_key, event_type)):
        raise ValueError('venue, key and type required')
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError('timezone-aware timestamp required')
    encoded = json.dumps(payload, sort_keys=True, allow_nan=False)
    cursor = db.execute("""INSERT OR IGNORE INTO workflow_outbox
        (venue_id,event_key,event_type,payload,next_attempt_at) VALUES (?,?,?,?,?)""",
        (venue_id,event_key,event_type,encoded,now.astimezone(timezone.utc).isoformat()))
    return cursor.rowcount == 1


def dispatch_mock(db: sqlite3.Connection, venue_id: str, now: datetime,
                  handler, max_attempts: int = 3) -> int:
    """Process due events for one venue; caller commits. Handler must be idempotent."""
    if not venue_id or max_attempts < 1 or now.tzinfo is None or now.utcoffset() is None:
        raise ValueError('invalid dispatch arguments')
    due = db.execute("""SELECT id,event_type,payload,attempts FROM workflow_outbox
        WHERE venue_id=? AND status='pending' AND next_attempt_at<=?
        ORDER BY id""", (venue_id, now.astimezone(timezone.utc).isoformat())).fetchall()
    delivered = 0
    for event_id, event_type, raw, attempts in due:
        try:
            handler(event_type, json.loads(raw))
        except Exception:
            attempts += 1
            status = 'dead' if attempts >= max_attempts else 'pending'
            retry_at = now.astimezone(timezone.utc) + timedelta(seconds=2 ** attempts)
            db.execute("""UPDATE workflow_outbox SET attempts=?,status=?,next_attempt_at=?
                WHERE id=? AND venue_id=? AND status='pending' """,
                (attempts,status,retry_at.isoformat(),event_id,venue_id))
        else:
            db.execute("""UPDATE workflow_outbox SET status='delivered',attempts=attempts+1
                WHERE id=? AND venue_id=? AND status='pending' """, (event_id,venue_id))
            delivered += 1
    return delivered
