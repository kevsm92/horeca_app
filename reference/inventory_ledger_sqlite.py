"""Offline synthetic SQLite inventory ledger. No API or external integrations."""
from decimal import Decimal, InvalidOperation
import sqlite3

UNITS = {"g", "ml", "each"}
REASONS = {"opening", "receive_mock", "consume_mock", "waste_mock", "count_adjustment"}

def connect(path):
    db = sqlite3.connect(path, timeout=10, isolation_level=None)
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("PRAGMA busy_timeout=10000")
    db.executescript("""
    CREATE TABLE IF NOT EXISTS ingredients (
      venue_id TEXT NOT NULL, ingredient_id TEXT NOT NULL,
      unit TEXT NOT NULL CHECK(unit IN ('g','ml','each')),
      PRIMARY KEY(venue_id,ingredient_id));
    CREATE TABLE IF NOT EXISTS stock_events (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      venue_id TEXT NOT NULL, ingredient_id TEXT NOT NULL,
      event_key TEXT NOT NULL, delta_milli INTEGER NOT NULL CHECK(delta_milli != 0),
      reason TEXT NOT NULL CHECK(reason IN
        ('opening','receive_mock','consume_mock','waste_mock','count_adjustment')),
      recorded_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
      UNIQUE(venue_id,event_key),
      FOREIGN KEY(venue_id,ingredient_id) REFERENCES ingredients(venue_id,ingredient_id));
    CREATE TRIGGER IF NOT EXISTS no_event_update BEFORE UPDATE ON stock_events
      BEGIN SELECT RAISE(ABORT,'immutable event'); END;
    CREATE TRIGGER IF NOT EXISTS no_event_delete BEFORE DELETE ON stock_events
      BEGIN SELECT RAISE(ABORT,'immutable event'); END;
    """)
    return db

def milli(value):
    try:
        v = Decimal(str(value))
        scaled = v * 1000
        if not v.is_finite() or scaled != scaled.to_integral_value():
            raise ValueError("quantity must have at most three decimals")
        n = int(scaled)
        if n == 0 or abs(n) > 10**12:
            raise ValueError("quantity out of range")
        return n
    except (InvalidOperation, TypeError, OverflowError) as exc:
        raise ValueError("invalid quantity") from exc

def add_ingredient(db, venue_id, ingredient_id, unit):
    if not venue_id or not ingredient_id or unit not in UNITS:
        raise ValueError("invalid ingredient")
    db.execute("INSERT INTO ingredients VALUES(?,?,?)", (venue_id,ingredient_id,unit))

def balance(db, venue_id, ingredient_id):
    return db.execute(
        "SELECT COALESCE(SUM(delta_milli),0) FROM stock_events WHERE venue_id=? AND ingredient_id=?",
        (venue_id,ingredient_id)).fetchone()[0]

def append_event(db, venue_id, ingredient_id, event_key, delta, reason):
    """Atomic admission; caller must authenticate and authorize venue before use."""
    if not all((venue_id,ingredient_id,event_key)) or reason not in REASONS:
        raise ValueError("invalid event metadata")
    amount = milli(delta)
    db.execute("BEGIN IMMEDIATE")
    try:
        existing = db.execute(
            "SELECT ingredient_id,delta_milli,reason FROM stock_events WHERE venue_id=? AND event_key=?",
            (venue_id,event_key)).fetchone()
        if existing:
            if existing != (ingredient_id,amount,reason):
                raise ValueError("idempotency key reused with different payload")
            result = balance(db,venue_id,ingredient_id)
            db.execute("COMMIT")
            return result
        if not db.execute(
            "SELECT 1 FROM ingredients WHERE venue_id=? AND ingredient_id=?",
            (venue_id,ingredient_id)).fetchone():
            raise ValueError("ingredient not found in venue")
        current = balance(db,venue_id,ingredient_id)
        if current + amount < 0:
            raise ValueError("insufficient stock")
        db.execute(
            "INSERT INTO stock_events(venue_id,ingredient_id,event_key,delta_milli,reason) VALUES(?,?,?,?,?)",
            (venue_id,ingredient_id,event_key,amount,reason))
        db.execute("COMMIT")
        return current + amount
    except BaseException:
        db.execute("ROLLBACK")
        raise
