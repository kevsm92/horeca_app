"""Offline SQLite no-show audit schema; not an authenticated API or transition handler."""

SCHEMA = """
CREATE TABLE IF NOT EXISTS reservation_no_show_audit (
    event_id TEXT PRIMARY KEY CHECK(length(trim(event_id)) > 0),
    venue_id TEXT NOT NULL CHECK(length(trim(venue_id)) > 0),
    reservation_id TEXT NOT NULL CHECK(length(trim(reservation_id)) > 0),
    actor_id TEXT NOT NULL CHECK(length(trim(actor_id)) > 0),
    occurred_utc TEXT NOT NULL CHECK(length(trim(occurred_utc)) > 0),
    previous_revision INTEGER NOT NULL CHECK(previous_revision >= 0),
    resulting_revision INTEGER NOT NULL CHECK(resulting_revision = previous_revision + 1),
    previous_status TEXT NOT NULL CHECK(previous_status = 'confirmed'),
    resulting_status TEXT NOT NULL CHECK(resulting_status = 'no_show'),
    UNIQUE(venue_id, reservation_id, resulting_revision)
);
CREATE TRIGGER IF NOT EXISTS no_show_audit_no_update
BEFORE UPDATE ON reservation_no_show_audit BEGIN SELECT RAISE(ABORT, 'audit immutable'); END;
CREATE TRIGGER IF NOT EXISTS no_show_audit_no_delete
BEFORE DELETE ON reservation_no_show_audit BEGIN SELECT RAISE(ABORT, 'audit immutable'); END;
"""

def install(conn):
    """Install audit schema on a caller-owned connection; no implicit commit."""
    conn.executescript(SCHEMA)
