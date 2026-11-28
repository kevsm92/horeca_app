"""Offline SQLite outbox producer. Caller must authorize venue; no dispatch."""
import json
from datetime import datetime, timezone
from uuid import uuid4

SCHEMA = """
CREATE TABLE IF NOT EXISTS workflow_outbox (
 event_id TEXT PRIMARY KEY,
 venue_id TEXT NOT NULL,
 event_type TEXT NOT NULL,
 event_version INTEGER NOT NULL CHECK(event_version >= 1),
 aggregate_id TEXT NOT NULL,
 aggregate_revision INTEGER NOT NULL CHECK(aggregate_revision >= 1),
 payload_json TEXT NOT NULL CHECK(json_valid(payload_json)),
 created_at_utc TEXT NOT NULL,
 available_at_utc TEXT NOT NULL,
 attempt_count INTEGER NOT NULL DEFAULT 0 CHECK(attempt_count >= 0),
 state TEXT NOT NULL DEFAULT 'pending' CHECK(state IN ('pending','leased','delivered','dead_letter')),
 lease_token TEXT, lease_expires_at_utc TEXT, last_error_code TEXT,
 UNIQUE(venue_id,event_type,aggregate_id,aggregate_revision)
);
"""

def initialize(db):
    db.executescript(SCHEMA)

def produce(db, *, venue_id, event_type, aggregate_id, aggregate_revision, payload, mutate):
    """Atomically invoke mutate(db) and enqueue one event; mutate must not commit."""
    if db.in_transaction:
        raise ValueError('producer requires an unowned transaction')
    if not all(isinstance(x, str) and x.strip() for x in (venue_id, event_type, aggregate_id)):
        raise ValueError('missing identity')
    if type(aggregate_revision) is not int or aggregate_revision < 1:
        raise ValueError('invalid revision')
    if event_type != 'operational.check_due.v1':
        raise ValueError('unsupported event type')
    if not isinstance(payload, dict) or set(payload) != {'check_id', 'sop_revision_id'}:
        raise ValueError('unsupported payload')
    if not all(isinstance(v, str) and v.startswith('synthetic-') for v in payload.values()):
        raise ValueError('synthetic identifiers required')
    body = json.dumps(payload, sort_keys=True, separators=(',', ':'))
    now = datetime.now(timezone.utc).isoformat()
    event_id = str(uuid4())
    db.execute('BEGIN IMMEDIATE')
    try:
        existing = db.execute("""SELECT event_id FROM workflow_outbox
            WHERE venue_id=? AND event_type=? AND aggregate_id=? AND aggregate_revision=?""",
            (venue_id, event_type, aggregate_id, aggregate_revision)).fetchone()
        if existing:
            db.commit()
            return existing[0], False
        mutate(db)
        db.execute("""INSERT INTO workflow_outbox
            (event_id,venue_id,event_type,event_version,aggregate_id,aggregate_revision,
             payload_json,created_at_utc,available_at_utc)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (event_id, venue_id, event_type, 1, aggregate_id, aggregate_revision, body, now, now))
        db.commit()
        return event_id, True
    except BaseException:
        db.rollback()
        raise
