"""Offline synthetic venue-scoped menu catalog; not an HTTP authentication layer."""
def initialize(connection):
    connection.execute("""CREATE TABLE IF NOT EXISTS menu_catalog_items (
        venue_id TEXT NOT NULL CHECK(length(venue_id) BETWEEN 1 AND 128),
        item_id TEXT NOT NULL CHECK(length(item_id) BETWEEN 1 AND 128),
        category TEXT NOT NULL CHECK(category IN ('food', 'drink')),
        name TEXT NOT NULL CHECK(length(name) BETWEEN 1 AND 160),
        price_cents INTEGER NOT NULL CHECK(price_cents BETWEEN 0 AND 100000000),
        available INTEGER NOT NULL CHECK(available IN (0, 1)),
        PRIMARY KEY (venue_id, item_id))""")

def upsert_item(connection, *, venue_id, item_id, category, name, price_cents, available):
    """Caller must derive venue from authenticated context; never from raw request input."""
    if any(not isinstance(x, str) or not x or len(x) > limit
           for x, limit in ((venue_id, 128), (item_id, 128), (name, 160))):
        raise ValueError('Invalid catalog identity/name')
    if category not in ('food', 'drink') or type(price_cents) is not int or not 0 <= price_cents <= 100000000 or type(available) is not bool:
        raise ValueError('Invalid catalog fields')
    connection.execute("""INSERT INTO menu_catalog_items VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(venue_id,item_id) DO UPDATE SET category=excluded.category,
        name=excluded.name, price_cents=excluded.price_cents,
        available=excluded.available""",
        (venue_id, item_id, category, name, price_cents, int(available)))

def list_items(connection, *, venue_id):
    """Return only this venue's catalog; venue must come from trusted session."""
    if not isinstance(venue_id, str) or not 0 < len(venue_id) <= 128:
        raise ValueError('Authenticated venue required')
    rows = connection.execute("""SELECT item_id,category,name,price_cents,available
        FROM menu_catalog_items WHERE venue_id=? ORDER BY category,name,item_id""", (venue_id,)).fetchall()
    return [dict(id=r[0], category=r[1], name=r[2], price_cents=r[3], available=bool(r[4]), currency='EUR') for r in rows]
