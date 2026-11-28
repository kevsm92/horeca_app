import unittest
from datetime import date, datetime
from zoneinfo import ZoneInfo
from roster_overlap import overlaps_roster_week
from weekly_roster import weekly_roster

TZ = ZoneInfo("Europe/Brussels")
WEEK = date(2026, 11, 30)


class RosterOverlapTests(unittest.TestCase):
    def test_previous_sunday_cross_midnight(self):
        start, end = datetime(2026, 11, 29, 23, tzinfo=TZ), datetime(2026, 11, 30, 2, tzinfo=TZ)
        self.assertTrue(overlaps_roster_week(start, end, WEEK))
        staff = [{"id": "fictional-a", "venue_id": "v1", "name": "Fictional Ada"}]
        shifts = [{"id": "overnight", "venue_id": "v1", "staff_id": "fictional-a", "station": "bar", "start": start, "end": end}]
        self.assertEqual([s["id"] for s in weekly_roster("v1", WEEK, shifts, staff)["shifts"]], ["overnight"])
        self.assertEqual(weekly_roster("v2", WEEK, shifts, staff)["shifts"], [])

    def test_exact_boundaries_are_exclusive(self):
        self.assertFalse(overlaps_roster_week(datetime(2026, 11, 29, 20, tzinfo=TZ), datetime(2026, 11, 30, 0, tzinfo=TZ), WEEK))
        self.assertFalse(overlaps_roster_week(datetime(2026, 12, 7, 0, tzinfo=TZ), datetime(2026, 12, 7, 2, tzinfo=TZ), WEEK))

    def test_end_of_week_crossover(self):
        self.assertTrue(overlaps_roster_week(datetime(2026, 12, 6, 23, tzinfo=TZ), datetime(2026, 12, 7, 2, tzinfo=TZ), WEEK))

    def test_naive_and_reverse_rejected(self):
        with self.assertRaises(ValueError):
            overlaps_roster_week(datetime(2026, 11, 30), datetime(2026, 12, 1, tzinfo=TZ), WEEK)
        with self.assertRaises(ValueError):
            overlaps_roster_week(datetime(2026, 12, 1, tzinfo=TZ), datetime(2026, 11, 30, tzinfo=TZ), WEEK)


if __name__ == "__main__":
    unittest.main()
