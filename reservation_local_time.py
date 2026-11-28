"""Resolve venue-local reservation timestamps without silently guessing at DST boundaries.

Offline helper; authorization, capacity, and booking policy are separate gates.
"""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def resolve_local_booking_time(wall_time: datetime, venue_timezone: str, *, fold: int | None = None) -> datetime:
    """Convert a naive wall time to UTC; ambiguous times require an explicit fold."""
    if not isinstance(wall_time, datetime) or wall_time.tzinfo is not None:
        raise ValueError("naive local datetime required")
    if not isinstance(venue_timezone, str) or not venue_timezone:
        raise ValueError("IANA timezone required")
    try:
        zone = ZoneInfo(venue_timezone)
    except (ZoneInfoNotFoundError, ValueError, TypeError) as exc:
        raise ValueError("unknown IANA timezone") from exc
    if fold is not None and (type(fold) is not int or fold not in (0, 1)):
        raise ValueError("fold must be 0 or 1")
    candidates = []
    for candidate_fold in (0, 1):
        local = wall_time.replace(tzinfo=zone, fold=candidate_fold)
        utc = local.astimezone(timezone.utc)
        if utc.astimezone(zone).replace(tzinfo=None) == wall_time and utc not in candidates:
            candidates.append(utc)
    if not candidates:
        raise ValueError("nonexistent local time")
    if len(candidates) == 2 and fold is None:
        raise ValueError("ambiguous local time requires fold")
    if len(candidates) == 2:
        return wall_time.replace(tzinfo=zone, fold=fold).astimezone(timezone.utc)
    if fold == 1:
        raise ValueError("fold=1 only valid for ambiguous local time")
    return candidates[0]


if __name__ == "__main__":
    import unittest

    class Tests(unittest.TestCase):
        def test_normal(self):
            self.assertEqual(resolve_local_booking_time(datetime(2026, 11, 15, 19), "Europe/Brussels"), datetime(2026, 11, 15, 18, tzinfo=timezone.utc))

        def test_gap(self):
            with self.assertRaisesRegex(ValueError, "nonexistent"):
                resolve_local_booking_time(datetime(2027, 3, 28, 2, 30), "Europe/Brussels")

        def test_overlap(self):
            wall = datetime(2027, 10, 31, 2, 30)
            with self.assertRaisesRegex(ValueError, "ambiguous"):
                resolve_local_booking_time(wall, "Europe/Brussels")
            self.assertEqual(resolve_local_booking_time(wall, "Europe/Brussels", fold=0), datetime(2027, 10, 31, 0, 30, tzinfo=timezone.utc))
            self.assertEqual(resolve_local_booking_time(wall, "Europe/Brussels", fold=1), datetime(2027, 10, 31, 1, 30, tzinfo=timezone.utc))

        def test_invalid(self):
            for args in [(datetime(2026, 11, 15, 19, tzinfo=timezone.utc), "Europe/Brussels"), (datetime(2026, 11, 15, 19), "Not/AZone")]:
                with self.assertRaises(ValueError):
                    resolve_local_booking_time(*args)
            with self.assertRaises(ValueError):
                resolve_local_booking_time(datetime(2026, 11, 15, 19), "Europe/Brussels", fold=True)
            with self.assertRaises(ValueError):
                resolve_local_booking_time(datetime(2026, 11, 15, 19), "Europe/Brussels", fold=1)

    unittest.main()
