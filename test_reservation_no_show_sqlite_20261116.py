"""Synthetic regression coverage for no-show transition."""
import sqlite3
import unittest
from reservation_no_show_sqlite import mark_no_show, NoShowConflict

class NoShowTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.execute("CREATE TABLE reservations(id TEXT,venue_id TEXT,status TEXT,revision INTEGER,PRIMARY KEY(id,venue_id))")
        self.db.executemany("INSERT INTO reservations VALUES(?,?,?,?)", [
            ("r1","a","confirmed",0),("r1","b","confirmed",0),("r2","a","seated",0)])
        self.db.commit()
        self.kw = dict(venue_id="a",reservation_id="r1",expected_revision=0,
            scheduled_utc="2026-11-16T18:00:00+00:00",
            now_utc="2026-11-16T18:15:00+00:00",grace_minutes=15,staff_confirmed=True)

    def tearDown(self):
        self.db.close()

    def test_boundary_and_tenant(self):
        self.assertEqual(mark_no_show(self.db,**self.kw),1)
        self.assertEqual(self.db.execute("SELECT status FROM reservations WHERE venue_id='b'").fetchone()[0],"confirmed")

    def test_requires_human_and_elapsed_grace(self):
        for change in ({"staff_confirmed":False},{"now_utc":"2026-11-16T18:14:59.999999+00:00"}):
            with self.assertRaises(NoShowConflict):
                mark_no_show(self.db,**(self.kw|change))

    def test_stale_and_cross_venue(self):
        mark_no_show(self.db,**self.kw)
        for change in ({},{"venue_id":"other"}):
            with self.assertRaises(NoShowConflict):
                mark_no_show(self.db,**(self.kw|change))

    def test_seated_rejected(self):
        with self.assertRaises(NoShowConflict):
            mark_no_show(self.db,**(self.kw|{"reservation_id":"r2"}))

    def test_invalid_timestamps_and_revision(self):
        for change in ({"now_utc":"2026-11-16T18:15:00"},{"expected_revision":True},{"grace_minutes":True}):
            with self.assertRaises(ValueError):
                mark_no_show(self.db,**(self.kw|change))

if __name__=="__main__":
    unittest.main()
