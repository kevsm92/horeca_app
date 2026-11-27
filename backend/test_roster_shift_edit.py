import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from roster_shift_edit import prepare_shift_edit


class ShiftEditTests(unittest.TestCase):
    def setUp(self):
        self.principal = SimpleNamespace(authenticated=True, role="manager", venue_id="demo-a")
        self.t = datetime(2026, 11, 30, 9, tzinfo=timezone.utc)
        self.first = dict(id="s1", venue_id="demo-a", staff_id="fictional-1", station="bar",
                          start_utc=self.t, end_utc=self.t + timedelta(hours=2))
        self.second = dict(id="s2", venue_id="demo-a", staff_id="fictional-1", station="bar",
                           start_utc=self.t + timedelta(hours=3), end_utc=self.t + timedelta(hours=5))
        self.snapshot = dict(venue_id="demo-a", revision=3, status="draft", shifts=[self.first, self.second])
        self.staff = [dict(id="fictional-1", venue_id="demo-a")]
        self.stations = [dict(id="bar", venue_id="demo-a")]

    def edit(self, **kwargs):
        args = dict(principal=self.principal, snapshot=self.snapshot, expected_revision=3,
                    shift_id="s1", replacement=self.first, staff=self.staff, stations=self.stations)
        args.update(kwargs)
        return prepare_shift_edit(**args)

    def test_valid_edit_immutable_and_cas(self):
        result = self.edit(replacement=dict(self.first, end_utc=self.t + timedelta(hours=3)))
        self.assertEqual(result["next_revision"], 4)
        self.assertTrue(result["requires_atomic_compare_and_swap"])
        self.assertEqual(result["shifts"][0]["end_utc"], (self.t + timedelta(hours=3)).isoformat())
        self.assertEqual(self.snapshot["shifts"][0]["end_utc"], self.t + timedelta(hours=2))

    def test_overlap(self):
        with self.assertRaisesRegex(ValueError, "overlap"):
            self.edit(replacement=dict(self.first, end_utc=self.t + timedelta(hours=4)))

    def test_auth_tenant_revision(self):
        for principal in [SimpleNamespace(authenticated=True, role="staff", venue_id="demo-a"),
                          SimpleNamespace(authenticated=False, role="manager", venue_id="demo-a"),
                          SimpleNamespace(authenticated=True, role="manager", venue_id="demo-b")]:
            with self.assertRaises(PermissionError):
                self.edit(principal=principal)
        for revision in (2, True):
            with self.assertRaises(ValueError):
                self.edit(expected_revision=revision)

    def test_published_duplicate_foreign(self):
        with self.assertRaises(ValueError):
            self.edit(snapshot=dict(self.snapshot, status="published"))
        with self.assertRaises(ValueError):
            self.edit(snapshot=dict(self.snapshot, shifts=[self.first, self.first]))
        for field, value in [("venue_id", "demo-b"), ("staff_id", "foreign"), ("station", "foreign")]:
            with self.assertRaises(ValueError):
                self.edit(replacement=dict(self.first, **{field: value}))

    def test_invalid_interval_identity(self):
        for replacement in [dict(self.first, start_utc=self.t.replace(tzinfo=None)),
                            dict(self.first, end_utc=self.t), dict(self.first, id="s3")]:
            with self.assertRaises(ValueError):
                self.edit(replacement=replacement)


if __name__ == "__main__":
    unittest.main()
