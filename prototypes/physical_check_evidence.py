"""Offline append-only physical inspection evidence. Synthetic fixtures only; not an API."""
import sqlite3
from datetime import datetime, timezone

DDL = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS checks (
 venue_id TEXT NOT NULL, check_id TEXT NOT NULL, sop_id TEXT NOT NULL,
 sop_revision INTEGER NOT NULL CHECK(sop_revision>0),
 state TEXT NOT NULL DEFAULT 'pending' CHECK(state IN ('pending','passed','deviation')),
 PRIMARY KEY(venue_id,check_id));
CREATE TABLE IF NOT EXISTS check_evidence (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 venue_id TEXT NOT NULL, check_id TEXT NOT NULL,
 actor_id TEXT NOT NULL, outcome TEXT NOT NULL
 CHECK(outcome IN ('pass','fail','not_performed')),
 observed_value TEXT, unit TEXT, instrument_id TEXT,
 recorded_at TEXT NOT NULL,
 FOREIGN KEY(venue_id,check_id) REFERENCES checks(venue_id,check_id));
CREATE TRIGGER IF NOT EXISTS check_evidence_no_update BEFORE UPDATE ON check_evidence
 BEGIN SELECT RAISE(ABORT,'immutable inspection evidence'); END;
CREATE TRIGGER IF NOT EXISTS check_evidence_no_delete BEFORE DELETE ON check_evidence
 BEGIN SELECT RAISE(ABORT,'immutable inspection evidence'); END;
"""

def connect(path=":memory:"):
    db = sqlite3.connect(path, isolation_level=None)
    db.executescript(DDL)
    return db

def schedule(db, *, venue_id, check_id, sop_id, sop_revision):
    if not all(isinstance(v,str) and v.strip() for v in (venue_id,check_id,sop_id)):
        raise ValueError("missing identifier")
    if type(sop_revision) is not int or sop_revision < 1:
        raise ValueError("invalid SOP revision")
    db.execute("INSERT INTO checks(venue_id,check_id,sop_id,sop_revision) VALUES(?,?,?,?)",
               (venue_id,check_id,sop_id,sop_revision))

def record(db, *, venue_id, check_id, actor_id, outcome,
           observed_value=None, unit=None, instrument_id=None):
    """Caller must authenticate actor and derive venue server-side before invocation."""
    if not all(isinstance(v,str) and v.strip() for v in (venue_id,check_id,actor_id)):
        raise ValueError("missing identifier")
    if outcome not in ('pass','fail','not_performed'):
        raise ValueError("invalid outcome")
    if (observed_value is None) != (unit is None):
        raise ValueError("measurement and unit must be supplied together")
    if outcome == 'not_performed' and observed_value is not None:
        raise ValueError("cannot measure a check not performed")
    with db:
        row = db.execute("SELECT state FROM checks WHERE venue_id=? AND check_id=?",
                         (venue_id,check_id)).fetchone()
        if row is None:
            raise ValueError("unknown venue-scoped check")
        # A prior failure is never overwritten with a pass. Recheck is a separate check.
        if row[0] != 'pending':
            raise ValueError("check already recorded; schedule a distinct recheck")
        db.execute("INSERT INTO check_evidence(venue_id,check_id,actor_id,outcome,observed_value,unit,instrument_id,recorded_at) VALUES(?,?,?,?,?,?,?,?)",
                   (venue_id,check_id,actor_id,outcome,observed_value,unit,instrument_id,
                    datetime.now(timezone.utc).isoformat()))
        db.execute("UPDATE checks SET state=? WHERE venue_id=? AND check_id=?",
                   ('passed' if outcome == 'pass' else 'deviation',venue_id,check_id))

if __name__ == "__main__":
    import unittest
    class InspectionTests(unittest.TestCase):
        def setUp(self):
            self.db = connect()
            schedule(self.db,venue_id="a",check_id="c",sop_id="chiller",sop_revision=2)
        def test_venue_isolation(self):
            with self.assertRaises(ValueError):
                record(self.db,venue_id="b",check_id="c",actor_id="fictional",outcome="pass")
            self.assertEqual(self.db.execute("SELECT count(*) FROM check_evidence").fetchone()[0],0)
        def test_failure_cannot_be_rewritten(self):
            record(self.db,venue_id="a",check_id="c",actor_id="fictional",outcome="fail")
            with self.assertRaises(ValueError):
                record(self.db,venue_id="a",check_id="c",actor_id="fictional",outcome="pass")
            self.assertEqual(self.db.execute("SELECT state FROM checks").fetchone()[0],"deviation")
        def test_immutable(self):
            record(self.db,venue_id="a",check_id="c",actor_id="fictional",outcome="pass")
            for sql in ("UPDATE check_evidence SET outcome='fail'","DELETE FROM check_evidence"):
                with self.assertRaises(sqlite3.IntegrityError):
                    self.db.execute(sql)
        def test_invalid_measurement(self):
            with self.assertRaises(ValueError):
                record(self.db,venue_id="a",check_id="c",actor_id="fictional",
                       outcome="not_performed",observed_value="3",unit="C")
    unittest.main()
