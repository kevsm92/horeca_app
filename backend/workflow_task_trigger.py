"""Offline idempotent task projection for leased operational.check_due.v1 events.

The caller must authorize venue access. No network or guest/staff messages.
"""
import json

SCHEMA = """CREATE TABLE IF NOT EXISTS workflow_mock_tasks (
    venue_id TEXT NOT NULL,
    event_id TEXT NOT NULL,
    check_id TEXT NOT NULL,
    sop_revision_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open' CHECK(status='open'),
    PRIMARY KEY(venue_id,event_id)
)"""

def initialize(db):
    db.execute(SCHEMA)

def project_check_due(db, *, venue_id, event):
    """Project a claimed event exactly once; caller controls transaction and ack.

    Returns True on insertion, False for duplicate. Never acknowledges the lease.
    """
    if not isinstance(venue_id, str) or not venue_id.strip():
        raise ValueError('venue required')
    if not isinstance(event, dict) or event.get('event_type') != 'operational.check_due.v1':
        raise ValueError('unsupported event')
    event_id = event.get('event_id')
    if not isinstance(event_id, str) or not event_id.strip():
        raise ValueError('event id required')
    try:
        payload = json.loads(event['payload_json'])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError('invalid event payload') from exc
    if not isinstance(payload, dict) or set(payload) != {'check_id', 'sop_revision_id'}:
        raise ValueError('invalid event payload shape')
    if not all(isinstance(v, str) and v.startswith('synthetic-') and len(v)>10 for v in payload.values()):
        raise ValueError('synthetic identifiers required')
    row = db.execute('SELECT venue_id,event_type,payload_json FROM workflow_outbox WHERE event_id=?',
                     (event_id,)).fetchone()
    if row != (venue_id, event['event_type'], event['payload_json']):
        raise ValueError('event venue or payload mismatch')
    cursor = db.execute('''INSERT OR IGNORE INTO workflow_mock_tasks
        (venue_id,event_id,check_id,sop_revision_id) VALUES (?,?,?,?)''',
        (venue_id,event_id,payload['check_id'],payload['sop_revision_id']))
    return cursor.rowcount == 1
