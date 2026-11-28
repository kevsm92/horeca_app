"""Week-window intersection for timezone-aware scheduled shifts (no attendance inference)."""
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo


def overlaps_roster_week(start: datetime, end: datetime, monday: date, timezone="Europe/Brussels") -> bool:
    """Include cross-boundary shifts, using half-open local calendar week intervals."""
    if not isinstance(monday, date) or isinstance(monday, datetime) or monday.weekday() != 0:
        raise ValueError("monday must be a Monday date")
    if any(not isinstance(t, datetime) or t.tzinfo is None or t.utcoffset() is None for t in (start, end)):
        raise ValueError("shift timestamps must include timezone")
    if end <= start:
        raise ValueError("shift must end after start")
    tz = ZoneInfo(timezone)
    week_start = datetime.combine(monday, time.min, tzinfo=tz)
    week_end = datetime.combine(monday + timedelta(days=7), time.min, tzinfo=tz)
    return start.astimezone(ZoneInfo("UTC")) < week_end.astimezone(ZoneInfo("UTC")) and end.astimezone(ZoneInfo("UTC")) > week_start.astimezone(ZoneInfo("UTC"))
