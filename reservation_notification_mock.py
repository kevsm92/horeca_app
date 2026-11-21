"""Offline mock reservation notification intent ledger. Never delivers messages."""
import json
from datetime import datetime, timezone

ALLOWED = frozenset({'waitlist_offer', 'reservation_cancelled', 'reservation_reminder'})

def initialize(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS reservation_notification_intents (
        venue_id TEXT NOT NULL, event_id TEXT NOT NULL, kind TEXT NOT NULL,
        reservation_id TEXT NOT NULL, payload_json TEXT NOT NULL,
        state TEXT NOT NULL DEFAULT 'mock_pending' CHECK(state='mock_pending'),
        PRIMARY KEY(venue_id, event_id))""")

def _validated(venue_id, event_id, kind, reservation_id, payload):
    if any(type(x) is not str or not x.strip() for x in (venue_id, event_id, reservation_id)):
        raise ValueError('identifiers required')
    if kind not in ALLOWED:
        raise ValueError('unsupported notification kind')
    if type(payload) is not dict or set(payload) != {'scheduled_utc'} or type(payload['scheduled_utc']) is not str:
        raise ValueError('only synthetic scheduled_utc metadata allowed')
    try:
        stamp = datetime.fromisoformat(payload['scheduled_utc'])
        if stamp.utcoffset() is None or stamp.utcoffset().total_seconds() != 0:
            raise ValueError
    except (ValueError, TypeError, AttributeError):
        raise ValueError('UTC timestamp required') from None
    canonical = json.dumps({'scheduled_utc': stamp.astimezone(timezone.utc).isoformat()}, sort_keys=True)
    return venue_id, event_id, kind, reservation_id, canonical

def enqueue_mock_in_transaction(conn, *, venue_id, event_id, kind, reservation_id, payload):
    """Insert in caller's active transaction; never commit or roll back it.

    Caller must authorize venue and write the trusted reservation event in
    the same SQLite transaction. This function never delivers messages.
    """
    if not conn.in_transaction:
        raise ValueError('active transaction required')
    venue_id, event_id, kind, reservation_id, canonical = _validated(venue_id, event_id, kind, reservation_id, payload)
    row = conn.execute('SELECT kind,reservation_id,payload_json FROM reservation_notification_intents WHERE venue_id=? AND event_id=?', (venue_id,event_id)).fetchone()
    wanted = (kind,reservation_id,canonical)
    if row is not None:
        if tuple(row) != wanted:
            raise ValueError('event id conflict')
        return False
    conn.execute('INSERT INTO reservation_notification_intents(venue_id,event_id,kind,reservation_id,payload_json) VALUES(?,?,?,?,?)', (venue_id,event_id,*wanted))
    return True

def enqueue_mock(conn, *, venue_id, event_id, kind, reservation_id, payload):
    """Standalone venue-scoped idempotent mock. Caller authorizes venue."""
    if conn.in_transaction:
        raise ValueError('existing transaction unsupported')
    conn.execute('BEGIN IMMEDIATE')
    try:
        inserted = enqueue_mock_in_transaction(conn, venue_id=venue_id, event_id=event_id, kind=kind, reservation_id=reservation_id, payload=payload)
        conn.commit()
        return inserted
    except BaseException:
        conn.rollback()
        raise
