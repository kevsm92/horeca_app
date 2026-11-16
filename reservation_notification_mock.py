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

def enqueue_mock(conn, *, venue_id, event_id, kind, reservation_id, payload):
    """Venue-scoped idempotent mock. Caller authorizes venue; no delivery."""
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
    if conn.in_transaction:
        raise ValueError('existing transaction unsupported')
    conn.execute('BEGIN IMMEDIATE')
    try:
        row = conn.execute('SELECT kind,reservation_id,payload_json FROM reservation_notification_intents WHERE venue_id=? AND event_id=?', (venue_id,event_id)).fetchone()
        wanted = (kind,reservation_id,canonical)
        if row is not None:
            if row != wanted:
                raise ValueError('event id conflict')
            conn.commit()
            return False
        conn.execute('INSERT INTO reservation_notification_intents(venue_id,event_id,kind,reservation_id,payload_json) VALUES(?,?,?,?,?)', (venue_id,event_id,*wanted))
        conn.commit()
        return True
    except BaseException:
        conn.rollback()
        raise
