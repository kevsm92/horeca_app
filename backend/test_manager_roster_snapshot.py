import sqlite3
import unittest
from types import SimpleNamespace
from manager_roster_snapshot import manager_roster_snapshot
from roster_revision_store import initialize, create_snapshot

class ManagerRosterSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        initialize(self.db)
        self.manager = SimpleNamespace(authenticated=True, role="manager", venue_id="fictional-a")
        create_snapshot(self.db, venue_id="fictional-a", week_start="2026-11-23", payload={
            "venue_id": "fictional-a", "status": "draft", "shifts": [
                {"id": "shift-1", "venue_id": "fictional-a", "staff_id": "fictional-staff"}]})

    def tearDown(self):
        self.db.close()

    def test_read_revision_and_no_presence_inference(self):
        result = manager_roster_snapshot(principal=self.manager, db=self.db, week_start="2026-11-23")
        self.assertEqual((result["revision"], result["status"], result["attendance"]), (0, "draft", "not_inferred"))
        self.assertEqual(len(result["shifts"]), 1)

    def test_missing_not_fake_zero(self):
        result = manager_roster_snapshot(principal=self.manager, db=self.db, week_start="2026-11-30")
        self.assertEqual((result["status"], result["revision"]), ("missing", None))

    def test_tenant_isolation(self):
        other = SimpleNamespace(authenticated=True, role="manager", venue_id="fictional-b")
        self.assertEqual(manager_roster_snapshot(principal=other, db=self.db, week_start="2026-11-23")["status"], "missing")

    def test_forbidden(self):
        for principal in (SimpleNamespace(authenticated=False, role="manager", venue_id="fictional-a"),
                          SimpleNamespace(authenticated=True, role="staff", venue_id="fictional-a")):
            with self.assertRaises(PermissionError):
                manager_roster_snapshot(principal=principal, db=self.db, week_start="2026-11-23")

    def test_invalid_week(self):
        with self.assertRaises(ValueError):
            manager_roster_snapshot(principal=self.manager, db=self.db, week_start="2026-11-24")

    def test_corrupt_cross_venue_shift(self):
        self.db.execute("UPDATE roster_snapshots SET payload=?", ('{"venue_id":"fictional-a","status":"draft","shifts":[{"venue_id":"fictional-b"}]}',))
        with self.assertRaises(ValueError):
            manager_roster_snapshot(principal=self.manager, db=self.db, week_start="2026-11-23")

if __name__ == "__main__":
    unittest.main()
