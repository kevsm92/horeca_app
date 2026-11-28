"""SQLite reservation write prototype. Synthetic data only; not integrated with API."""
import sqlite3
import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone

SCHEMA = """
CREATE TABLE tables(venue TEXT, id TEXT, capacity INTEGER CHECK(capacity>0), PRIMARY KEY(venue,id));
CREATE TABLE bookings(venue TEXT, id TEXT, table_id TEXT, party INTEGER CHECK(party>0),
 start_us INTEGER, end_us INTEGER, turnover_us INTEGER,
 status TEXT CHECK(status IN ('confirmed','seated','cancelled')),
 PRIMARY KEY(venue,id), FOREIGN KEY(venue,table_id) REFERENCES tables(venue,id));
"""

def us(t):
    if not isinstance(t, datetime) or t.tzinfo is None or t.utcoffset() is None:
        raise ValueError("timezone-aware datetime required")
    return int(t.astimezone(timezone.utc).timestamp() * 1000000)

def reserve(db, venue, booking_id, table_id, party, start, duration, turnover):
    if not all(isinstance(s,str) and s.strip() for s in (venue,booking_id,table_id)):
        raise ValueError("identifiers required")
    if type(party) is not int or party < 1 or not isinstance(duration,timedelta) or duration <= timedelta(0) or not isinstance(turnover,timedelta) or turnover < timedelta(0):
        raise ValueError("invalid parameters")
    a, b = us(start), us(start + duration)
    gap = turnover // timedelta(microseconds=1)
    db.execute("BEGIN IMMEDIATE")
    try:
        row = db.execute("SELECT capacity FROM tables WHERE venue=? AND id=?", (venue,table_id)).fetchone()
        if row is None or party > row[0]:
            raise ValueError("unknown table or insufficient capacity")
        overlap = db.execute("""SELECT 1 FROM bookings WHERE venue=? AND table_id=?
          AND status IN ('confirmed','seated') AND ? < end_us+turnover_us
          AND start_us < ? LIMIT 1""", (venue,table_id,a,b+gap)).fetchone()
        if overlap:
            raise ValueError("reservation conflict")
        db.execute("INSERT INTO bookings VALUES(?,?,?,?,?,?,?,'confirmed')", (venue,booking_id,table_id,party,a,b,gap))
        db.commit()
    except BaseException:
        db.rollback()
        raise

class AtomicReservationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = self.temp.name + "/bookings.db"
        with self.connect() as db:
            db.executescript(SCHEMA)
            db.executemany("INSERT INTO tables VALUES(?,?,?)", [("a","t1",4),("b","t1",2)])
        self.start = datetime(2026,11,15,18,tzinfo=timezone.utc)
    def tearDown(self):
        self.temp.cleanup()
    def connect(self):
        db = sqlite3.connect(self.path, timeout=5, isolation_level=None)
        db.execute("PRAGMA foreign_keys=ON")
        return db
    def book(self, db, ident, venue="a", table="t1", party=2, at=None):
        reserve(db,venue,ident,table,party,at or self.start,timedelta(hours=1),timedelta(minutes=15))
    def test_competing_writers(self):
        barrier = threading.Barrier(2)
        results = []
        def run(i):
            with self.connect() as db:
                barrier.wait()
                try:
                    self.book(db,str(i))
                    results.append("ok")
                except ValueError:
                    results.append("conflict")
        threads = [threading.Thread(target=run,args=(i,)) for i in range(2)]
        for t in threads: t.start()
        for t in threads: t.join(timeout=8)
        self.assertFalse(any(t.is_alive() for t in threads))
        self.assertCountEqual(results,["ok","conflict"])
    def test_turnover_boundary(self):
        with self.connect() as db:
            self.book(db,"one")
            with self.assertRaisesRegex(ValueError,"conflict"):
                self.book(db,"two",at=self.start+timedelta(hours=1))
            self.book(db,"three",at=self.start+timedelta(hours=1,minutes=15))
    def test_tenant_and_capacity(self):
        with self.connect() as db:
            self.book(db,"one")
            self.book(db,"one",venue="b")
            with self.assertRaisesRegex(ValueError,"capacity"):
                self.book(db,"large",venue="b",party=3,at=self.start+timedelta(hours=2))
            with self.assertRaisesRegex(ValueError,"unknown table"):
                self.book(db,"missing",table="t2")
    def test_rollback(self):
        with self.connect() as db:
            self.book(db,"one")
            with self.assertRaises(ValueError): self.book(db,"conflict")
            self.book(db,"later",at=self.start+timedelta(hours=2))
            self.assertEqual(db.execute("SELECT COUNT(*) FROM bookings").fetchone()[0],2)
    def test_invalid_and_duplicate(self):
        with self.connect() as db:
            with self.assertRaises(ValueError): self.book(db,"bad",party=True)
            with self.assertRaises(ValueError): self.book(db,"bad",at=self.start.replace(tzinfo=None))
            self.book(db,"one")
            with self.assertRaises(sqlite3.IntegrityError):
                self.book(db,"one",at=self.start+timedelta(hours=2))

if __name__ == "__main__":
    unittest.main()
