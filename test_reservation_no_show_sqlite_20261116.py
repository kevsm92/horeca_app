"""Synthetic regression coverage for no-show transition."""
import sqlite3
import unittest
from reservation_no_show_sqlite import mark_no_show, NoShowConflict

class NoShowTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.execute("CREATE TABLE reservations(id TEXT,venue_id TEXT,status TEXT,revision INTEGER,scheduled_utc TEXT,PRIMARY KEY(id,venue_id))")
        self.db.executemany("INSERT INTO reservations VALUES(?,?,?,?,?)", [
            ("r1","a","confirmed",0,"2026-11-16T18:00:00+00:00"),("r1","b","confirmed",0,"2026-11-16T18:00:00+00:00"),("r2","a","seated",0,"2026-11-16T18:00:00+00:00")])
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

    def test_rejects_caller_schedule_substitution(self):
        with self.assertRaisesRegex(NoShowConflict, "stale booking schedule"):
            mark_no_show(self.db, **(self.kw | {"scheduled_utc": "2026-11-15T18:00:00+00:00"}))
        self.assertEqual(self.db.execute("SELECT revision FROM reservations WHERE id='r1' AND venue_id='a'").fetchone()[0], 0)

    def test_reschedule_must_observe_new_grace(self):
        self.db.execute("UPDATE reservations SET scheduled_utc=? WHERE id='r1' AND venue_id='a'", ("2026-11-16T19:00:00+00:00",))
        self.db.commit()
        with self.assertRaisesRegex(NoShowConflict, "stale booking schedule"):
            mark_no_show(self.db, **self.kw)
        with self.assertRaisesRegex(NoShowConflict, "grace period not elapsed"):
            mark_no_show(self.db, **(self.kw | {"scheduled_utc": "2026-11-16T19:00:00+00:00"}))

    def test_corrupt_persisted_schedule_rejected(self):
        self.db.execute("UPDATE reservations SET scheduled_utc='bad' WHERE id='r1' AND venue_id='a'")
        self.db.commit()
        with self.assertRaisesRegex(NoShowConflict, "invalid persisted schedule"):
            mark_no_show(self.db, **self.kw)

if __name__=="__main__":
    unittest.main()
