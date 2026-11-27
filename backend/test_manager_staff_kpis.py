import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from manager_staff_kpis import manager_staff_kpis

NOW = datetime(2026, 11, 27, 20, tzinfo=timezone.utc)


class StaffKpiTests(unittest.TestCase):
    def setUp(self):
        self.principal = SimpleNamespace(authenticated=True, role="manager", venue_id="fictional-a")
        self.shifts = [
            dict(venue_id="fictional-a", staff_id="a", start_utc=NOW-timedelta(hours=1), end_utc=NOW+timedelta(hours=1)),
            dict(venue_id="fictional-b", staff_id="b", start_utc=NOW-timedelta(hours=1), end_utc=NOW+timedelta(hours=1)),
        ]

    def test_missing_punch_source_is_not_zero(self):
        result = manager_staff_kpis(principal=self.principal, shifts=self.shifts, active_punches=None, as_of=NOW)
        self.assertEqual(result["scheduled_staff"]["value"], 1)
        self.assertIsNone(result["clocked_in_staff"]["value"])
        self.assertEqual(result["clocked_in_staff"]["status"], "unavailable")
        self.assertFalse(result["attendance_inferred_from_schedule"])

    def test_distinct_present_and_tenant_isolation(self):
        punches = [dict(venue_id="fictional-a", staff_id="x", clocked_in=True),
                   dict(venue_id="fictional-a", staff_id="x", clocked_in=True),
                   dict(venue_id="fictional-b", staff_id="b", clocked_in=True)]
        result = manager_staff_kpis(principal=self.principal, shifts=self.shifts, active_punches=punches, as_of=NOW)
        self.assertEqual(result["clocked_in_staff"]["value"], 1)
        self.assertEqual(result["scheduled_staff"]["value"], 1)

    def test_authorization(self):
        for role, auth in [("staff", True), ("manager", False)]:
            with self.assertRaises(PermissionError):
                manager_staff_kpis(principal=SimpleNamespace(role=role, authenticated=auth, venue_id="fictional-a"),
                                   shifts=[], active_punches=[], as_of=NOW)

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):
            manager_staff_kpis(principal=self.principal, shifts=self.shifts, active_punches=[], as_of=NOW.replace(tzinfo=None))
        with self.assertRaises(ValueError):
            manager_staff_kpis(principal=self.principal, shifts=[], active_punches=[
                dict(venue_id="fictional-a", staff_id="a", clocked_in=None)], as_of=NOW)


if __name__ == "__main__":
    unittest.main(verbosity=2)
