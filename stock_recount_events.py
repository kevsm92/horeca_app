"""Offline append-only venue-scoped recount events; never posts inventory."""
import sqlite3
from datetime import datetime

SCHEMA = """
CREATE TABLE IF NOT EXISTS stock_recount_events (
 event_id TEXT PRIMARY KEY, venue_id TEXT NOT NULL, sku_id TEXT NOT NULL,
 recount_id TEXT NOT NULL, event_type TEXT NOT NULL
 CHECK(event_type IN ('count_recorded','recount_recorded','dispute_flagged')),
 actor_id TEXT NOT NULL, ledger_revision INTEGER NOT NULL CHECK(ledger_revision >= 0),
 quantity_milli INTEGER NOT NULL CHECK(quantity_milli >= 0), occurred_at TEXT NOT NULL,
 UNIQUE(venue_id,recount_id,event_type)
);
CREATE INDEX IF NOT EXISTS recount_scope ON stock_recount_events(venue_id,sku_id,recount_id);
CREATE TRIGGER IF NOT EXISTS recount_no_update BEFORE UPDATE ON stock_recount_events
BEGIN SELECT RAISE(ABORT,'immutable recount event'); END;
CREATE TRIGGER IF NOT EXISTS recount_no_delete BEFORE DELETE ON stock_recount_events
BEGIN SELECT RAISE(ABORT,'immutable recount event'); END;
"""

def initialize(conn):
    conn.executescript(SCHEMA)

def record_event(conn, *, event_id, venue_id, sku_id, recount_id, event_type,
                 actor_id, ledger_revision, quantity_milli, occurred_at):
    for name, value in [('event_id',event_id),('venue_id',venue_id),('sku_id',sku_id),
                        ('recount_id',recount_id),('actor_id',actor_id)]:
        if not isinstance(value,str) or not value.strip():
            raise ValueError(f'{name} required')
    if event_type not in ('count_recorded','recount_recorded','dispute_flagged'):
        raise ValueError('unknown event type')
    for name,value in [('ledger_revision',ledger_revision),('quantity_milli',quantity_milli)]:
        if type(value) is not int or value < 0:
            raise ValueError(f'{name} must be nonnegative integer')
    if not isinstance(occurred_at,str):
        raise ValueError('timestamp required')
    try:
        parsed = datetime.fromisoformat(occurred_at)
    except ValueError as exc:
        raise ValueError('invalid timestamp') from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError('timezone-aware timestamp required')
    # Caller must resolve actor, venue, clock and revision from trusted storage.
    # Acquire write lock BEFORE checking scope; reject caller-owned transactions.
    if conn.in_transaction:
        raise ValueError('record_event requires an idle SQLite connection')
    conn.execute('BEGIN IMMEDIATE')
    try:
        bound = conn.execute(
            'SELECT venue_id,sku_id FROM stock_recount_events WHERE recount_id=? LIMIT 1',
            (recount_id,)).fetchone()
        if bound and bound != (venue_id,sku_id):
            raise ValueError('recount identity bound to another scope')
        conn.execute("""INSERT INTO stock_recount_events
            (event_id,venue_id,sku_id,recount_id,event_type,actor_id,
             ledger_revision,quantity_milli,occurred_at)
             VALUES (?,?,?,?,?,?,?,?,?)""",
            (event_id,venue_id,sku_id,recount_id,event_type,actor_id,
             ledger_revision,quantity_milli,occurred_at))
        conn.commit()
    except BaseException:
        conn.rollback()
        raise

def list_events(conn, *, venue_id, sku_id, recount_id):
    if not all(isinstance(x,str) and x.strip() for x in (venue_id,sku_id,recount_id)):
        raise ValueError('scope required')
    return conn.execute("""SELECT event_id,event_type,actor_id,ledger_revision,
        quantity_milli,occurred_at FROM stock_recount_events
        WHERE venue_id=? AND sku_id=? AND recount_id=? ORDER BY rowid""",
        (venue_id,sku_id,recount_id)).fetchall()
