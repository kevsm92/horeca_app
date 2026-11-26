"""Offline synthetic weekly roster snapshot. No attendance inference or HTTP exposure."""
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import sqlite3

BRUSSELS = ZoneInfo("Europe/Brussels")

def init_schema(db):
    db.executescript("""
    PRAGMA foreign_keys=ON;
    CREATE TABLE IF NOT EXISTS roster_staff(
      venue_id TEXT NOT NULL, staff_id TEXT NOT NULL, display_name TEXT NOT NULL,
      station TEXT NOT NULL, PRIMARY KEY(venue_id,staff_id));
    CREATE TABLE IF NOT EXISTS roster_shifts(
      venue_id TEXT NOT NULL, shift_id TEXT NOT NULL, staff_id TEXT NOT NULL,
      starts_at TEXT NOT NULL, ends_at TEXT NOT NULL,
      PRIMARY KEY(venue_id,shift_id),
      FOREIGN KEY(venue_id,staff_id) REFERENCES roster_staff(venue_id,staff_id));
    """)

def week_snapshot(db, *, venue_id, monday):
    """Return scheduled staff and overlapping shifts; presence is unknown."""
    if not venue_id or not isinstance(monday,date) or monday.weekday()!=0:
        raise ValueError("venue and Monday date required")
    start=datetime.combine(monday,datetime.min.time(),BRUSSELS).astimezone(timezone.utc)
    end=datetime.combine(monday+timedelta(days=7),datetime.min.time(),BRUSSELS).astimezone(timezone.utc)
    rows=db.execute("""
      SELECT s.staff_id,s.display_name,s.station,h.shift_id,h.starts_at,h.ends_at
      FROM roster_staff s LEFT JOIN roster_shifts h
        ON h.venue_id=s.venue_id AND h.staff_id=s.staff_id
        AND h.starts_at < ? AND h.ends_at > ?
      WHERE s.venue_id=? ORDER BY s.staff_id,h.starts_at
    """,(end.isoformat(),start.isoformat(),venue_id)).fetchall()
    staff={}
    for sid,name,station,shift_id,beg,finish in rows:
        item=staff.setdefault(sid,{"id":sid,"name":name,"station":station,"shifts":[]})
        if shift_id is not None:
            item["shifts"].append({"id":shift_id,"start":beg,"end":finish,"attendance":"unknown"})
    return {"venue_id":venue_id,"week_start":monday.isoformat(),
            "source":"scheduled_roster","staff":list(staff.values())}

def add_shift(db, *, venue_id, shift_id, staff_id, start, end):
    """Insert an offline shift with timezone and overlap guards."""
    if not all((venue_id,shift_id,staff_id)) or start.tzinfo is None or end.tzinfo is None:
        raise ValueError("identifiers and aware timestamps required")
    if end<=start:
        raise ValueError("end must follow start")
    begin=start.astimezone(timezone.utc).isoformat()
    finish=end.astimezone(timezone.utc).isoformat()
    with db:
        if db.execute("""SELECT 1 FROM roster_shifts WHERE venue_id=? AND staff_id=?
                         AND starts_at < ? AND ends_at > ?""",
                      (venue_id,staff_id,finish,begin)).fetchone():
            raise ValueError("overlapping shift")
        db.execute("INSERT INTO roster_shifts VALUES (?,?,?,?,?)",
                   (venue_id,shift_id,staff_id,begin,finish))

if __name__=="__main__":
    import unittest
    class RosterTests(unittest.TestCase):
        def setUp(self):
            self.db=sqlite3.connect(":memory:")
            init_schema(self.db)
            self.db.executemany("INSERT INTO roster_staff VALUES (?,?,?,?)",
                [("a","s1","Fictional Ada","Kitchen"),("b","s1","Fictional Bea","Bar")])
            self.start=datetime(2026,11,30,9,tzinfo=BRUSSELS)
            self.end=datetime(2026,11,30,17,tzinfo=BRUSSELS)
        def test_tenant_and_presence(self):
            add_shift(self.db,venue_id="a",shift_id="x",staff_id="s1",start=self.start,end=self.end)
            a=week_snapshot(self.db,venue_id="a",monday=date(2026,11,30))
            b=week_snapshot(self.db,venue_id="b",monday=date(2026,11,30))
            self.assertEqual(a["staff"][0]["shifts"][0]["attendance"],"unknown")
            self.assertEqual(b["staff"][0]["shifts"],[])
        def test_overlap_and_foreign_key(self):
            add_shift(self.db,venue_id="a",shift_id="x",staff_id="s1",start=self.start,end=self.end)
            with self.assertRaises(ValueError):
                add_shift(self.db,venue_id="a",shift_id="y",staff_id="s1",start=self.start,end=self.end)
            with self.assertRaises(sqlite3.IntegrityError):
                add_shift(self.db,venue_id="a",shift_id="z",staff_id="missing",start=self.start,end=self.end)
        def test_invalid_inputs(self):
            with self.assertRaises(ValueError):
                week_snapshot(self.db,venue_id="a",monday=date(2026,12,1))
            with self.assertRaises(ValueError):
                add_shift(self.db,venue_id="a",shift_id="x",staff_id="s1",
                          start=datetime(2026,11,30,9),end=self.end)
    unittest.main(verbosity=2)
