"""Offline SQLite ingredient stock ledger; synthetic data only.

Quantities are integer g/ml/each. Caller must authenticate and authorize venue.
"""
import sqlite3
import unittest

UNITS = {'g', 'ml', 'each'}

def initialize(db):
    db.execute('PRAGMA foreign_keys=ON')
    db.executescript("""
    CREATE TABLE IF NOT EXISTS ingredients(
      venue_id TEXT NOT NULL, ingredient_id TEXT NOT NULL, name TEXT NOT NULL,
      unit TEXT NOT NULL CHECK(unit IN ('g','ml','each')),
      PRIMARY KEY(venue_id,ingredient_id));
    CREATE TABLE IF NOT EXISTS stock_events(
      venue_id TEXT NOT NULL, event_id TEXT NOT NULL, ingredient_id TEXT NOT NULL,
      delta INTEGER NOT NULL CHECK(delta != 0), reason TEXT NOT NULL,
      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY(venue_id,event_id),
      FOREIGN KEY(venue_id,ingredient_id) REFERENCES ingredients(venue_id,ingredient_id));
    CREATE TRIGGER IF NOT EXISTS stock_no_update BEFORE UPDATE ON stock_events
      BEGIN SELECT RAISE(ABORT,'immutable ledger'); END;
    CREATE TRIGGER IF NOT EXISTS stock_no_delete BEFORE DELETE ON stock_events
      BEGIN SELECT RAISE(ABORT,'immutable ledger'); END;
    """)

def ident(value):
    if not isinstance(value,str) or not 1 <= len(value) <= 100 or not value.isascii() or not all(c.isalnum() or c in '-_' for c in value):
        raise ValueError('invalid identifier')
    return value

def add_ingredient(db,venue,ingredient,name,unit):
    venue,ingredient=ident(venue),ident(ingredient)
    if not isinstance(name,str) or not name.strip() or len(name)>120 or unit not in UNITS:
        raise ValueError('invalid ingredient')
    with db:
        db.execute('INSERT INTO ingredients VALUES(?,?,?,?)',(venue,ingredient,name.strip(),unit))

def balance(db,venue,ingredient):
    venue,ingredient=ident(venue),ident(ingredient)
    if db.execute('SELECT 1 FROM ingredients WHERE venue_id=? AND ingredient_id=?',(venue,ingredient)).fetchone() is None:
        raise ValueError('ingredient not found in venue')
    return db.execute('SELECT COALESCE(SUM(delta),0) FROM stock_events WHERE venue_id=? AND ingredient_id=?',(venue,ingredient)).fetchone()[0]

def post_event(db,venue,ingredient,event,delta,reason):
    """Returns False on identical retry; conflicts and negative stock raise."""
    venue,ingredient,event=map(ident,(venue,ingredient,event))
    if type(delta) is not int or delta==0 or abs(delta)>10**12 or not isinstance(reason,str) or reason not in {'receipt','use','waste','correction'}:
        raise ValueError('invalid stock event')
    if (reason=='receipt' and delta<0) or (reason in {'use','waste'} and delta>0):
        raise ValueError('stock movement sign does not match reason')
    db.execute('BEGIN IMMEDIATE')
    try:
        old=db.execute('SELECT ingredient_id,delta,reason FROM stock_events WHERE venue_id=? AND event_id=?',(venue,event)).fetchone()
        if old is not None:
            if old!=(ingredient,delta,reason):
                raise ValueError('conflicting idempotency key')
            db.commit()
            return False
        if balance(db,venue,ingredient)+delta<0:
            raise ValueError('insufficient stock')
        db.execute('INSERT INTO stock_events(venue_id,event_id,ingredient_id,delta,reason) VALUES(?,?,?,?,?)',(venue,event,ingredient,delta,reason))
        db.commit()
        return True
    except BaseException:
        db.rollback()
        raise

class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(':memory:',isolation_level=None)
        initialize(self.db)
        add_ingredient(self.db,'a','flour','Flour','g')
        add_ingredient(self.db,'b','flour','Flour','g')
    def tearDown(self):
        self.db.close()
    def test_receipt_use(self):
        post_event(self.db,'a','flour','r',500,'receipt')
        post_event(self.db,'a','flour','u',-120,'use')
        self.assertEqual(balance(self.db,'a','flour'),380)
    def test_duplicate(self):
        post_event(self.db,'a','flour','r',500,'receipt')
        self.assertFalse(post_event(self.db,'a','flour','r',500,'receipt'))
        self.assertEqual(balance(self.db,'a','flour'),500)
    def test_conflict(self):
        post_event(self.db,'a','flour','r',500,'receipt')
        with self.assertRaises(ValueError):
            post_event(self.db,'a','flour','r',501,'receipt')
    def test_negative_rollback(self):
        with self.assertRaises(ValueError):
            post_event(self.db,'a','flour','u',-1,'use')
        self.assertEqual(balance(self.db,'a','flour'),0)
    def test_tenant(self):
        post_event(self.db,'a','flour','r',10,'receipt')
        self.assertEqual(balance(self.db,'b','flour'),0)
        with self.assertRaises(ValueError):
            post_event(self.db,'b','missing','x',1,'receipt')
    def test_immutable(self):
        post_event(self.db,'a','flour','r',10,'receipt')
        for sql in ("UPDATE stock_events SET delta=1","DELETE FROM stock_events"):
            with self.assertRaises(sqlite3.IntegrityError):
                self.db.execute(sql)
    def test_units_and_quantities(self):
        with self.assertRaises(ValueError):
            add_ingredient(self.db,'a','oil','Oil','litres')
        for delta in (0,1.5,True,10**13):
            with self.assertRaises(ValueError):
                post_event(self.db,'a','flour','bad',delta,'receipt')
    def test_reason_sign_rejected_without_ledger_mutation(self):
        for event,delta,reason in [('bad-receipt',-1,'receipt'),
                                   ('bad-use',1,'use'),('bad-waste',1,'waste')]:
            with self.assertRaises(ValueError):
                post_event(self.db,'a','flour',event,delta,reason)
        self.assertEqual(balance(self.db,'a','flour'),0)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM stock_events').fetchone()[0],0)

    def test_valid_signs_and_correction_unchanged(self):
        self.assertTrue(post_event(self.db,'a','flour','r',10,'receipt'))
        self.assertTrue(post_event(self.db,'a','flour','u',-2,'use'))
        self.assertTrue(post_event(self.db,'a','flour','w',-1,'waste'))
        self.assertTrue(post_event(self.db,'a','flour','c',1,'correction'))
        self.assertEqual(balance(self.db,'a','flour'),8)

    def test_malformed_reason_rejected_without_writes(self):
        for reason in (None, [], {}, 7, True, 'unknown'):
            with self.subTest(reason=repr(reason)):
                with self.assertRaises(ValueError):
                    post_event(self.db,'a','flour','malformed',1,reason)
        self.assertEqual(balance(self.db,'a','flour'),0)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM stock_events').fetchone()[0],0)

    def test_event_ids_venue_scoped(self):
        post_event(self.db,'a','flour','r',10,'receipt')
        post_event(self.db,'b','flour','r',20,'receipt')
        self.assertEqual(balance(self.db,'b','flour'),20)

if __name__=='__main__':
    unittest.main()
