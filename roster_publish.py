"""Offline manager-only roster publication marker; no notifications or attendance inference."""
from datetime import date


class PublishConflict(ValueError):
    pass


def init_publish_schema(db):
    db.execute('''CREATE TABLE IF NOT EXISTS roster_publications (
        venue_id TEXT NOT NULL, week_monday TEXT NOT NULL,
        published_revision INTEGER NOT NULL CHECK(published_revision > 0),
        PRIMARY KEY (venue_id, week_monday))''')


def publish_week(db, *, principal, monday: date, expected_revision: int):
    """Publish only the exact persisted draft revision; return published revision."""
    if (not getattr(principal, 'authenticated', False)
            or getattr(principal, 'role', None) not in ('manager', 'owner')
            or not getattr(principal, 'staff_id', None)
            or not getattr(principal, 'venue_id', None)):
        raise PermissionError('authenticated manager required')
    if not isinstance(monday, date) or monday.weekday() != 0:
        raise ValueError('Monday required')
    if type(expected_revision) is not int or expected_revision <= 0:
        raise ValueError('positive integer revision required')
    with db:
        db.execute('BEGIN IMMEDIATE')
        row = db.execute('''SELECT revision FROM roster_versions
            WHERE venue_id=? AND week_monday=?''',
            (principal.venue_id, monday.isoformat())).fetchone()
        if row is None or row[0] != expected_revision:
            raise PublishConflict('missing or changed draft')
        db.execute('''INSERT INTO roster_publications VALUES (?,?,?)
            ON CONFLICT(venue_id, week_monday) DO UPDATE SET
            published_revision=excluded.published_revision''',
            (principal.venue_id, monday.isoformat(), expected_revision))
    return expected_revision


def published_revision(db, *, principal, monday: date):
    if (not getattr(principal, 'authenticated', False)
            or getattr(principal, 'role', None) not in ('manager', 'owner')
            or not getattr(principal, 'venue_id', None)):
        raise PermissionError('authenticated manager required')
    row = db.execute('''SELECT published_revision FROM roster_publications
        WHERE venue_id=? AND week_monday=?''',
        (principal.venue_id, monday.isoformat())).fetchone()
    return row[0] if row else None
