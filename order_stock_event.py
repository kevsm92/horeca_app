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
    """)


def record_order_consumption(connection, *, venue_id, event_id, order_id, ingredients):
    """Write one atomic deduction per ingredient; duplicates are replay-safe.

    Caller must derive venue_id from authenticated server context, not request body.
    Ingredient amounts are positive integer milliunits in a prevalidated recipe unit.
    This does not check stock availability or send a real order.
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
    with connection:
        existing = connection.execute(
            'SELECT payload FROM order_stock_events WHERE venue_id=? AND event_id=?',
            (venue_id, event_id)).fetchone()
        if existing:
            if existing[0] != payload:
                raise ValueError('Event ID reused with different payload')
            return False
        connection.execute('INSERT INTO order_stock_events VALUES (?,?,?,?)',
                           (venue_id, event_id, order_id, payload))
        connection.executemany('INSERT INTO order_stock_ledger VALUES (?,?,?,?)',
            [(venue_id, event_id, ingredient_id, -amount)
             for ingredient_id, amount in sorted(ingredients.items())])
    return True
