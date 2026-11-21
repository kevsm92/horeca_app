"""Offline synthetic menu catalog prototype; not an authenticated HTTP service."""
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS menu_items (
 venue_id TEXT NOT NULL CHECK(length(venue_id) > 0),
 item_id TEXT NOT NULL CHECK(length(item_id) > 0),
 kind TEXT NOT NULL CHECK(kind IN ('food','drink')),
 name TEXT NOT NULL CHECK(length(name) > 0),
 price_cents INTEGER NOT NULL CHECK(price_cents >= 0),
 available INTEGER NOT NULL CHECK(available IN (0,1)),
 PRIMARY KEY (venue_id, item_id)
);
"""


def initialize(db):
    db.executescript(SCHEMA)


def add_item(db, *, venue_id, item_id, kind, name, price_cents, available=True):
    """Caller must authorize venue_id; never accept it from a public request."""
    if not isinstance(price_cents, int) or isinstance(price_cents, bool):
        raise ValueError('price_cents must be an integer')
    if not isinstance(available, bool):
        raise ValueError('available must be boolean')
    with db:
        db.execute('INSERT INTO menu_items VALUES (?,?,?,?,?,?)',
                   (venue_id, item_id, kind, name, price_cents, int(available)))


def list_items(db, *, authorized_venue_id):
    """Venue ID must come from an authenticated, authorized server-side principal."""
    if not authorized_venue_id:
        raise ValueError('authorized venue required')
    rows = db.execute('SELECT item_id, kind, name, price_cents, available '
                      'FROM menu_items WHERE venue_id=? ORDER BY item_id',
                      (authorized_venue_id,)).fetchall()
    return [{'id': r[0], 'type': r[1], 'name': r[2],
             'price_cents': r[3], 'currency': 'EUR', 'available': bool(r[4])}
            for r in rows]
