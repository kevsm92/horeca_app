"""Offline venue-scoped atomic weekly roster store; no HTTP or attendance inference."""
import json
from roster_revision import propose_revision

def init_schema(db):
    db.execute("""CREATE TABLE IF NOT EXISTS roster_versions (
        venue_id TEXT NOT NULL, week_monday TEXT NOT NULL,
        revision INTEGER NOT NULL CHECK(revision >= 0),
        shifts_json TEXT NOT NULL, PRIMARY KEY(venue_id, week_monday))""")

def _authorize(principal):
    if (not getattr(principal, "authenticated", False)
            or getattr(principal, "role", None) not in ("manager", "owner")
            or not getattr(principal, "venue_id", None)):
        raise PermissionError("manager session required")
    return principal.venue_id

def save_week(db, *, principal, monday, expected_revision, shifts):
    """Caller must provide a verified session principal; SQLite serializes writers."""
    venue = _authorize(principal)
    if monday.weekday() != 0:
        raise ValueError("Monday required")
    if type(expected_revision) is not int or not isinstance(shifts, tuple):
        raise ValueError("invalid revision or shifts")
    with db:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("SELECT revision FROM roster_versions WHERE venue_id=? AND week_monday=?",
                         (venue, monday.isoformat())).fetchone()
        revision = propose_revision(
            current_revision=row[0] if row else 0, expected_revision=expected_revision,
            current_venue=venue, requested_venue=venue, shifts=shifts)
        for shift in shifts:
            if not (monday <= shift.starts_at.date() < monday.fromordinal(monday.toordinal()+7)):
                raise ValueError("shift starts outside roster week")
        payload = json.dumps([dict(staff_id=s.staff_id, station_id=s.station_id,
            starts_at=s.starts_at.isoformat(), ends_at=s.ends_at.isoformat()) for s in shifts],
            sort_keys=True)
        db.execute("""INSERT INTO roster_versions VALUES (?,?,?,?)
            ON CONFLICT(venue_id,week_monday) DO UPDATE SET
            revision=excluded.revision, shifts_json=excluded.shifts_json""",
            (venue, monday.isoformat(), revision, payload))
    return revision

def read_week(db, *, principal, monday):
    venue = _authorize(principal)
    row = db.execute("SELECT revision, shifts_json FROM roster_versions WHERE venue_id=? AND week_monday=?",
                     (venue, monday.isoformat())).fetchone()
    return dict(revision=row[0] if row else 0, shifts=json.loads(row[1]) if row else [])
