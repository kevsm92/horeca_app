"""Offline, venue-scoped idempotent order-to-stock event prototype (synthetic only)."""
import json
import sqlite3


def initialize(connection):
    connection.executescript("""
    PRAGMA foreign_keys=ON;
    CREATE TABLE IF NOT EXISTS order_stock_events (
      venue_id TEXT NOT NULL, event_id TEXT NOT NULL, order_id TEXT NOT NULL,
      payload TEXT NOT NULL, PRIMARY KEY(venue_id,event_id));
    CREATE TABLE IF NOT EXISTS order_stock_ledger (
      venue_id TEXT NOT NULL, event_id TEXT NOT NULL, ingredient_id TEXT NOT NULL,
      delta_milliunits INTEGER NOT NULL CHECK(delta_milliunits < 0),
      PRIMARY KEY(venue_id,event_id,ingredient_id),
      FOREIGN KEY(venue_id,event_id) REFERENCES order_stock_events(venue_id,event_id));
    CREATE TRIGGER IF NOT EXISTS order_stock_ledger_no_update
      BEFORE UPDATE ON order_stock_ledger
      BEGIN SELECT RAISE(ABORT, 'immutable order stock ledger'); END;
    CREATE TRIGGER IF NOT EXISTS order_stock_ledger_no_delete
      BEFORE DELETE ON order_stock_ledger
      BEGIN SELECT RAISE(ABORT, 'immutable order stock ledger'); END;
    CREATE TRIGGER IF NOT EXISTS order_stock_events_no_update
      BEFORE UPDATE ON order_stock_events
      BEGIN SELECT RAISE(ABORT, 'immutable order stock event'); END;
    CREATE TRIGGER IF NOT EXISTS order_stock_events_no_delete
      BEFORE DELETE ON order_stock_events
      BEGIN SELECT RAISE(ABORT, 'immutable order stock event'); END;
    """)


def record_order_consumption(connection, *, venue_id, event_id, order_id, ingredients):
    """Atomically write one deduction per ingredient; concurrent retries are replay-safe.

    Caller must derive venue_id from authenticated server context, not request body.
    Ingredient amounts are positive integer milliunits in a prevalidated recipe unit.
    This does not check stock availability or send a real order.
    Requires ownership of a connection without an active transaction.
    """
    for value in (venue_id, event_id, order_id):
        if not isinstance(value, str) or not value or len(value) > 128:
            raise ValueError('Invalid event identity')
    if not isinstance(ingredients, dict) or not ingredients:
        raise ValueError('Ingredients required')
    if any(not isinstance(k, str) or not k or len(k) > 128 or
           type(v) is not int or v <= 0 or v > 1_000_000_000
           for k, v in ingredients.items()):
        raise ValueError('Invalid ingredient quantity')
    payload = json.dumps({'order_id': order_id, 'ingredients': ingredients}, sort_keys=True, separators=(',', ':'))
    if connection.in_transaction:
        raise ValueError('Dedicated connection required: transaction already active')
    # Acquire writer lock before checking idempotency, preventing two connections
    # from both observing an absent event before either inserts.
    connection.execute('BEGIN IMMEDIATE')
    try:
        existing = connection.execute(
            'SELECT payload FROM order_stock_events WHERE venue_id=? AND event_id=?',
            (venue_id, event_id)).fetchone()
        if existing:
            if existing[0] != payload:
                raise ValueError('Event ID reused with different payload')
            connection.commit()
            return False
        connection.execute('INSERT INTO order_stock_events VALUES (?,?,?,?)',
                           (venue_id, event_id, order_id, payload))
        connection.executemany('INSERT INTO order_stock_ledger VALUES (?,?,?,?)',
            [(venue_id, event_id, ingredient_id, -amount)
             for ingredient_id, amount in sorted(ingredients.items())])
        connection.commit()
        return True
    except BaseException:
        connection.rollback()
        raise
