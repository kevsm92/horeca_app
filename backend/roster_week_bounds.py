"""Convert venue-local Monday roster weeks to half-open UTC intervals.

Use overlap SQL (shift_end > start AND shift_start < end) for cross-week shifts.
"""
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo


def week_bounds_utc(day: date, timezone_name: str = "Europe/Brussels") -> tuple[datetime, datetime]:
    """Monday 00:00 inclusive to next Monday exclusive, respecting DST."""
    if not isinstance(day, date) or isinstance(day, datetime):
        raise TypeError("day must be a date")
    zone = ZoneInfo(timezone_name)
    monday = day - timedelta(days=day.weekday())
    start = datetime.combine(monday, time.min, zone).astimezone(timezone.utc)
    end = datetime.combine(monday + timedelta(days=7), time.min, zone).astimezone(timezone.utc)
    return start, end


if __name__ == "__main__":
    import unittest

    class WeekBoundsTests(unittest.TestCase):
        def test_standard_week(self):
            self.assertEqual(week_bounds_utc(date(2026, 11, 28)),
                             (datetime(2026, 11, 22, 23, tzinfo=timezone.utc),
                              datetime(2026, 11, 29, 23, tzinfo=timezone.utc)))

        def test_spring_dst_week_is_167_hours(self):
            start, end = week_bounds_utc(date(2027, 3, 28))
            self.assertEqual((end - start).total_seconds() / 3600, 167)

        def test_autumn_dst_week_is_169_hours(self):
            start, end = week_bounds_utc(date(2027, 10, 31))
            self.assertEqual((end - start).total_seconds() / 3600, 169)

        def test_same_week_for_each_day(self):
            self.assertEqual(week_bounds_utc(date(2026, 11, 23)),
                             week_bounds_utc(date(2026, 11, 29)))

        def test_reject_datetime(self):
            with self.assertRaises(TypeError):
                week_bounds_utc(datetime.now(timezone.utc))

    unittest.main()
