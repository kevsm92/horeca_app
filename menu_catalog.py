"""Offline synthetic, venue-scoped menu catalog; no HTTP exposure or live orders."""
import sqlite3


def initialize(db):
    db.execute('PRAGMA foreign_keys=ON')
    db.execute('''CREATE TABLE IF NOT EXISTS menu_item (
        venue_id TEXT NOT NULL CHECK(length(trim(venue_id)) > 0),
        item_id TEXT NOT NULL CHECK(length(trim(item_id)) > 0),
        category TEXT NOT NULL CHECK(category IN ('food', 'drink')),
        name TEXT NOT NULL CHECK(length(trim(name)) > 0),
        price_cents INTEGER NOT NULL CHECK(price_cents BETWEEN 0 AND 100000000),
        currency TEXT NOT NULL DEFAULT 'EUR' CHECK(currency = 'EUR'),
        available INTEGER NOT NULL CHECK(available IN (0, 1)),
        description TEXT,
        PRIMARY KEY (venue_id, item_id)
    )''')


def add_item(db, venue_id, item_id, category, name, price_cents, available=True, description=None):
    if type(price_cents) is not int or type(available) is not bool:
        raise ValueError('price must be integer cents; availability must be boolean')
    if description is not None and (not isinstance(description, str) or len(description) > 500):
        raise ValueError('invalid description')
    with db:
        db.execute('''INSERT INTO menu_item
          (venue_id,item_id,category,name,price_cents,available,description)
          VALUES (?,?,?,?,?,?,?)''',
          (venue_id,item_id,category,name,price_cents,int(available),description))


def list_items(db, venue_id):
    if not isinstance(venue_id, str) or not venue_id.strip():
        raise ValueError('venue scope required')
    return [dict(id=row[0], category=row[1], name=row[2], price_cents=row[3],
                 currency=row[4], available=bool(row[5]), description=row[6])
            for row in db.execute('''SELECT item_id,category,name,price_cents,currency,
                                           available,description FROM menu_item
                                    WHERE venue_id=? ORDER BY category,item_id''', (venue_id,))]


def seed_fictional(db, venue_id):
    """Idempotent example-only rows; does not replace venue-authored catalog data."""
    for item in [('demo-food-1','food','Fictional Vegetable Bowl',1250),
                 ('demo-drink-1','drink','Fictional Sparkling Water',350)]:
        with db:
            db.execute('''INSERT OR IGNORE INTO menu_item
                (venue_id,item_id,category,name,price_cents,available)
                VALUES (?,?,?,?,?,1)''', (venue_id,*item))
