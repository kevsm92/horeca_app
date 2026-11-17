"""Offline venue-scoped SQLite menu catalog. NOT an HTTP API.

Only pass a server-authenticated and authorized venue ID to list_items.
"""
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS menu_items (
 venue_id TEXT NOT NULL CHECK(length(trim(venue_id)) > 0),
 item_id TEXT NOT NULL CHECK(length(trim(item_id)) > 0),
 kind TEXT NOT NULL CHECK(kind IN ('food','drink')),
 name TEXT NOT NULL CHECK(length(trim(name)) > 0),
 price_cents INTEGER NOT NULL CHECK(typeof(price_cents)='integer' AND price_cents BETWEEN 0 AND 10000000),
 available INTEGER NOT NULL DEFAULT 1 CHECK(available IN (0,1)),
 description TEXT,
 PRIMARY KEY(venue_id,item_id)
);
CREATE INDEX IF NOT EXISTS menu_items_venue_kind ON menu_items(venue_id,kind);
"""

def connect(path):
    db = sqlite3.connect(str(path))
    db.row_factory = sqlite3.Row
    db.executescript(SCHEMA)
    return db

def list_items(db, *, authorized_venue_id, kind=None):
    if not isinstance(authorized_venue_id,str) or not authorized_venue_id.strip():
        raise ValueError('authorized venue required')
    if kind is not None and kind not in ('food','drink'):
        raise ValueError('invalid kind')
    sql = 'SELECT item_id,kind,name,price_cents,available,description FROM menu_items WHERE venue_id=?'
    params = [authorized_venue_id]
    if kind:
        sql += ' AND kind=?'
        params.append(kind)
    sql += ' ORDER BY kind,name,item_id'
    return [dict(row) | {'available':bool(row['available'])} for row in db.execute(sql,params)]

def seed_synthetic(db, *, venue_id):
    if not isinstance(venue_id,str) or not venue_id.strip():
        raise ValueError('venue required')
    with db:
        db.executemany("""INSERT OR IGNORE INTO menu_items
        (venue_id,item_id,kind,name,price_cents,available,description)
        VALUES (?,?,?,?,?,?,?)""", [
          (venue_id,'demo-food-1','food','Fictional Tomato Soup',650,1,'Synthetic example'),
          (venue_id,'demo-drink-1','drink','Fictional Sparkling Water',320,1,'Synthetic example')
        ])
