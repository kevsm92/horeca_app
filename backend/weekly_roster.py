"""Offline synthetic-only weekly roster projection; never infers attendance."""
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
import unittest
from roster_overlap import overlaps_roster_week

BRUSSELS = ZoneInfo("Europe/Brussels")


def weekly_roster(venue_id, week_start, shifts, staff):
    """Project trusted repository records; HTTP callers must enforce auth/RBAC."""
    if not isinstance(venue_id, str) or not venue_id:
        raise ValueError("venue required")
    if not isinstance(week_start, date) or isinstance(week_start, datetime) or week_start.weekday() != 0:
        raise ValueError("week_start must be a Monday date")
    end_day = week_start + timedelta(days=7)
    people = {p["id"]: p for p in staff if p["venue_id"] == venue_id}
    output = []
    for shift in shifts:
        if shift["venue_id"] != venue_id or shift["staff_id"] not in people:
            continue
        start, end = shift["start"], shift["end"]
        if any(not isinstance(t, datetime) or t.tzinfo is None or t.utcoffset() is None for t in (start, end)):
            raise ValueError("shift timestamps must include timezone")
        if end <= start:
            raise ValueError("shift must end after start")
        local_start = start.astimezone(BRUSSELS)
        local_end = end.astimezone(BRUSSELS)
        if not overlaps_roster_week(start, end, week_start):
            continue
        output.append({"id": shift["id"], "staff_id": shift["staff_id"],
                       "staff_name": people[shift["staff_id"]]["name"],
                       "station": shift["station"], "start": local_start.isoformat(),
                       "end": local_end.isoformat(), "status": "scheduled"})
    return {"venue_id": venue_id, "week_start": week_start.isoformat(),
            "timezone": "Europe/Brussels", "attendance": "unavailable",
            "shifts": sorted(output, key=lambda s: (s["start"], s["id"]))}


class WeeklyRosterTests(unittest.TestCase):
    def setUp(self):
        self.staff = [{"id": "a", "venue_id": "v1", "name": "Fictional Ada"},
                      {"id": "b", "venue_id": "v2", "name": "Fictional Bea"}]
        self.shifts = [dict(id="s1", venue_id="v1", staff_id="a", station="bar",
                            start=datetime(2026, 11, 30, 22, tzinfo=BRUSSELS),
                            end=datetime(2026, 12, 1, 2, tzinfo=BRUSSELS)),
                       dict(id="s2", venue_id="v2", staff_id="b", station="kitchen",
                            start=datetime(2026, 11, 30, 9, tzinfo=BRUSSELS),
                            end=datetime(2026, 11, 30, 17, tzinfo=BRUSSELS))]

    def test_venue_isolation_and_no_presence_inference(self):
        result = weekly_roster("v1", date(2026, 11, 30), self.shifts, self.staff)
        self.assertEqual([s["id"] for s in result["shifts"]], ["s1"])
        self.assertEqual(result["attendance"], "unavailable")
        self.assertEqual(result["shifts"][0]["status"], "scheduled")
        self.assertIn("2026-12-01T02:00:00", result["shifts"][0]["end"])

    def test_other_venue(self):
        self.assertEqual([s["id"] for s in weekly_roster("v2", date(2026, 11, 30), self.shifts, self.staff)["shifts"]], ["s2"])

    def test_invalid_week_and_naive_timestamp(self):
        with self.assertRaises(ValueError):
            weekly_roster("v1", date(2026, 12, 1), self.shifts, self.staff)
        bad = [dict(self.shifts[0], start=datetime(2026, 11, 30, 22))]
        with self.assertRaises(ValueError):
            weekly_roster("v1", date(2026, 11, 30), bad, self.staff)

    def test_empty_week_not_fabricated(self):
        self.assertEqual(weekly_roster("v1", date(2026, 12, 7), self.shifts, self.staff)["shifts"], [])


if __name__ == "__main__":
    unittest.main()
