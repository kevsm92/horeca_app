"""Focused synthetic tests for offline roster persistence."""
import sqlite3
import unittest
from datetime import date, datetime, timedelta, timezone
from roster_store import init_schema, save_week, read_week
from roster_revision import Shift, RosterConflict
from roster_manager_read import Principal

MON = date(2026, 11, 30)
A = Principal("mgr-a", "a", "manager", True)
B = Principal("mgr-b", "b", "manager", True)
S = Shift("fictional-1", datetime(2026,11,30,9,tzinfo=timezone.utc),
          datetime(2026,11,30,17,tzinfo=timezone.utc), "kitchen")

class RosterStoreTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        init_schema(self.db)

    def test_revision_and_isolation(self):
        self.assertEqual(save_week(self.db, principal=A, monday=MON,
                                   expected_revision=0, shifts=(S,)), 1)
        self.assertEqual(read_week(self.db, principal=A, monday=MON)["revision"], 1)
        self.assertEqual(read_week(self.db, principal=B, monday=MON)["shifts"], [])
        with self.assertRaises(RosterConflict):
            save_week(self.db, principal=A, monday=MON, expected_revision=0, shifts=())
        self.assertEqual(read_week(self.db, principal=A, monday=MON)["revision"], 1)

    def test_reject_unauthorized(self):
        with self.assertRaises(PermissionError):
            save_week(self.db, principal=Principal("x","a","staff",True),
                      monday=MON, expected_revision=0, shifts=(S,))
        with self.assertRaises(PermissionError):
            read_week(self.db, principal=Principal("x","a","manager",False), monday=MON)

    def test_invalid_does_not_mutate(self):
        overlapping = Shift("fictional-1", S.starts_at,
                            S.ends_at + timedelta(hours=1), "bar")
        with self.assertRaises(RosterConflict):
            save_week(self.db, principal=A, monday=MON,
                      expected_revision=0, shifts=(S, overlapping))
        self.assertEqual(read_week(self.db, principal=A, monday=MON)["revision"], 0)

    def test_week_boundary(self):
        late = Shift("fictional-1", S.starts_at+timedelta(days=7),
                     S.ends_at+timedelta(days=7), "bar")
        with self.assertRaises(ValueError):
            save_week(self.db, principal=A, monday=MON,
                      expected_revision=0, shifts=(late,))
        self.assertEqual(read_week(self.db, principal=A, monday=MON)["revision"], 0)

if __name__ == "__main__":
    unittest.main()
