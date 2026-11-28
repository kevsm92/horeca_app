"""Pure offline no-show review queue. Never changes a booking or contacts guests.

Caller must authorize venue and provide trusted reservation records.
"""
from datetime import datetime, timedelta, timezone


def _utc(value):
    if not isinstance(value, str):
        raise ValueError("UTC timestamp required")
    try:
        parsed = datetime.fromisoformat(value)
        if parsed.utcoffset() is None or parsed.utcoffset() != timedelta(0):
            raise ValueError
        return parsed.astimezone(timezone.utc)
    except (ValueError, TypeError, AttributeError):
        raise ValueError("UTC timestamp required") from None


def review_candidates(*, venue_id, reservations, now_utc, grace_minutes):
    """Select confirmed bookings after grace for human review; no mutation."""
    if type(venue_id) is not str or not venue_id.strip():
        raise ValueError("venue required")
    if type(grace_minutes) is not int or not 0 <= grace_minutes <= 1440:
        raise ValueError("invalid grace")
    now = _utc(now_utc)
    result = []
    seen = set()
    for item in reservations:
        if item["venue_id"] != venue_id or item["status"] != "confirmed":
            continue
        if (type(item["id"]) is not str or not item["id"].strip()
                or type(item["revision"]) is not int or item["revision"] < 0):
            raise ValueError("invalid trusted booking")
        if item["id"] in seen:
            raise ValueError("duplicate reservation ID in review snapshot")
        seen.add(item["id"])
        scheduled = _utc(item["scheduled_utc"])
        if now < scheduled + timedelta(minutes=grace_minutes):
            continue
        result.append({"reservation_id": item["id"], "expected_revision": item["revision"],
                       "scheduled_utc": scheduled.isoformat(), "staff_review_required": True})
    return sorted(result, key=lambda x: (x["scheduled_utc"], x["reservation_id"]))
