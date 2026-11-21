"""Append-only, venue-scoped supplier price history (offline synthetic prototype).

Run: python -m unittest -v supplier_price_history
"""
import sqlite3
from datetime import datetime
import unittest


def initialize_history(db):
    db.execute('PRAGMA foreign_keys=ON')
    db.executescript('''
    CREATE TABLE IF NOT EXISTS supplier_price_revision (
      venue_id TEXT NOT NULL, supplier_id TEXT NOT NULL, sku TEXT NOT NULL,
      revision INTEGER NOT NULL CHECK(revision > 0),
      price_cents INTEGER NOT NULL CHECK(price_cents >= 0),
      reason TEXT NOT NULL CHECK(length(trim(reason)) > 0),
      recorded_at TEXT NOT NULL CHECK(length(trim(recorded_at)) > 0),
      PRIMARY KEY (venue_id,supplier_id,sku,revision),
      FOREIGN KEY (venue_id,supplier_id,sku)
        REFERENCES supplier_sku(venue_id,supplier_id,sku)
    );
    CREATE TRIGGER IF NOT EXISTS supplier_price_revision_no_update
      BEFORE UPDATE ON supplier_price_revision BEGIN
        SELECT RAISE(ABORT,'price history is append-only'); END;
    CREATE TRIGGER IF NOT EXISTS supplier_price_revision_no_delete
      BEFORE DELETE ON supplier_price_revision BEGIN
        SELECT RAISE(ABORT,'price history is append-only'); END;
    ''')


def record_price_revision(db, venue_id, supplier_id, sku, price_cents, reason, recorded_at):
    """Record a historical quote; does NOT change current supplier SKU price."""
    if any(not isinstance(x, str) or not x.strip() for x in
           (venue_id, supplier_id, sku, reason, recorded_at)):
        raise ValueError('nonempty scope, reason and timestamp required')
    if type(price_cents) is not int or price_cents < 0:
        raise ValueError('price must be nonnegative integer cents')
    # Require canonical UTC to avoid ambiguous revision timestamps.
    try:
        parsed = datetime.strptime(recorded_at, '%Y-%m-%dT%H:%M:%SZ')
    except ValueError as exc:
        raise ValueError('recorded_at must be a valid UTC timestamp YYYY-MM-DDTHH:MM:SSZ') from exc
    if parsed.strftime('%Y-%m-%dT%H:%M:%SZ') != recorded_at:
        raise ValueError('recorded_at must be canonical UTC')
    with db:
        row = db.execute('''SELECT COALESCE(MAX(revision),0)+1 FROM supplier_price_revision
                            WHERE venue_id=? AND supplier_id=? AND sku=?''',
                         (venue_id,supplier_id,sku)).fetchone()
        revision = row[0]
        db.execute('''INSERT INTO supplier_price_revision
                      VALUES (?,?,?,?,?,?,?)''',
                   (venue_id,supplier_id,sku,revision,price_cents,reason,recorded_at))
    return revision


class PriceHistoryTests(unittest.TestCase):
    def setUp(self):
        from supplier_directory import initialize, add_supplier, add_sku
        self.db = sqlite3.connect(':memory:')
        initialize(self.db)
        for venue in ('a','b'):
            add_supplier(self.db,venue,'vendor','Synthetic Vendor')
            add_sku(self.db,venue,'vendor','sku','flour','kg',1,100,2)
        initialize_history(self.db)

    def tearDown(self):
        self.db.close()

    def test_revision_increments_and_preserves_current_quote(self):
        self.assertEqual(record_price_revision(self.db,'a','vendor','sku',110,'new quote','2026-11-21T01:00:00Z'),1)
        self.assertEqual(record_price_revision(self.db,'a','vendor','sku',120,'new quote','2026-11-21T02:00:00Z'),2)
        self.assertEqual(self.db.execute("SELECT price_cents FROM supplier_sku WHERE venue_id='a'").fetchone()[0],100)

    def test_venue_isolation_and_cross_venue_reference(self):
        record_price_revision(self.db,'a','vendor','sku',110,'quote','2026-11-21T01:00:00Z')
        self.assertEqual(self.db.execute("SELECT count(*) FROM supplier_price_revision WHERE venue_id='b'").fetchone()[0],0)
        with self.assertRaises(sqlite3.IntegrityError):
            record_price_revision(self.db,'c','vendor','sku',100,'quote','2026-11-21T01:00:00Z')

    def test_append_only_triggers(self):
        record_price_revision(self.db,'a','vendor','sku',110,'quote','2026-11-21T01:00:00Z')
        for sql in ("UPDATE supplier_price_revision SET price_cents=1",
                    "DELETE FROM supplier_price_revision"):
            with self.assertRaisesRegex(sqlite3.IntegrityError,'append-only'):
                self.db.execute(sql)

    def test_timestamp_validation_rejects_ambiguous_or_impossible_instants(self):
        for timestamp in ('2026-11-21', '2026-11-21T01:00:00',
                          '2026-11-21T02:00:00+01:00', '2026-02-30T01:00:00Z',
                          '2026-11-21T1:00:00Z', '2026-11-21T01:00:00.000Z'):
            with self.subTest(timestamp=timestamp), self.assertRaises(ValueError):
                record_price_revision(self.db,'a','vendor','sku',110,'quote',timestamp)
        self.assertEqual(self.db.execute('SELECT count(*) FROM supplier_price_revision').fetchone()[0],0)

    def test_invalid_prices_and_missing_provenance(self):
        for price in (-1,True,1.5):
            with self.assertRaises(ValueError):
                record_price_revision(self.db,'a','vendor','sku',price,'quote','2026-11-21T01:00:00Z')
        with self.assertRaises(ValueError):
            record_price_revision(self.db,'a','vendor','sku',100,'','2026-11-21T01:00:00Z')


if __name__ == '__main__':
    unittest.main()
