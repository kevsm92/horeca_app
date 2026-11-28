"""Offline venue-scoped supplier directory; no purchasing or network I/O."""
import sqlite3

def initialize(db):
    db.execute("PRAGMA foreign_keys=ON")
    db.executescript("""
    CREATE TABLE IF NOT EXISTS supplier (
      venue_id TEXT NOT NULL CHECK(length(trim(venue_id))>0),
      supplier_id TEXT NOT NULL CHECK(length(trim(supplier_id))>0),
      display_name TEXT NOT NULL CHECK(length(trim(display_name))>0),
      active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)),
      PRIMARY KEY(venue_id,supplier_id)
    );
    CREATE TABLE IF NOT EXISTS supplier_sku (
      venue_id TEXT NOT NULL,
      supplier_id TEXT NOT NULL,
      sku TEXT NOT NULL CHECK(length(trim(sku))>0),
      ingredient_id TEXT NOT NULL CHECK(length(trim(ingredient_id))>0),
      unit TEXT NOT NULL CHECK(unit IN ('g','kg','ml','l','each')),
      pack_quantity INTEGER NOT NULL CHECK(pack_quantity>0),
      price_cents INTEGER NOT NULL CHECK(price_cents>=0),
      lead_days INTEGER NOT NULL CHECK(lead_days BETWEEN 0 AND 365),
      currency TEXT NOT NULL DEFAULT 'EUR' CHECK(currency='EUR'),
      PRIMARY KEY(venue_id,supplier_id,sku),
      FOREIGN KEY(venue_id,supplier_id) REFERENCES supplier(venue_id,supplier_id)
    );
    """)

def add_supplier(db, venue_id, supplier_id, display_name):
    with db:
        db.execute('INSERT INTO supplier(venue_id,supplier_id,display_name) VALUES(?,?,?)',
                   (venue_id,supplier_id,display_name))

def add_sku(db, venue_id, supplier_id, sku, ingredient_id, unit, pack_quantity, price_cents, lead_days):
    if type(pack_quantity) is not int or type(price_cents) is not int or type(lead_days) is not int:
        raise ValueError('quantities, cents and lead days must be integers')
    with db:
        db.execute("""INSERT INTO supplier_sku
            (venue_id,supplier_id,sku,ingredient_id,unit,pack_quantity,price_cents,lead_days)
            VALUES(?,?,?,?,?,?,?,?)""",
            (venue_id,supplier_id,sku,ingredient_id,unit,pack_quantity,price_cents,lead_days))

def list_skus(db, venue_id, ingredient_id):
    if not venue_id or not ingredient_id:
        raise ValueError('venue and ingredient are required')
    return db.execute("""SELECT s.supplier_id,s.display_name,k.sku,k.unit,k.pack_quantity,
                                k.price_cents,k.lead_days
                         FROM supplier_sku k JOIN supplier s
                           ON s.venue_id=k.venue_id AND s.supplier_id=k.supplier_id
                         WHERE k.venue_id=? AND k.ingredient_id=? AND s.active=1
                         ORDER BY k.price_cents,k.supplier_id,k.sku""",
                      (venue_id,ingredient_id)).fetchall()
