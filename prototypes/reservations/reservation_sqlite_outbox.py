"""Offline reservation transitions and transactional mock notification outbox.

Synthetic only. No recipient data, delivery mechanism, network, or authorization API.
Caller must authenticate and authorize the venue before invoking this module.
"""
import hashlib
import json
import sqlite3
import unittest
from datetime import datetime, timezone

ALLOWED = {"held": {"confirmed", "cancelled"}, "confirmed": {"cancelled", "no_show"}, "cancelled": set(), "no_show": set()}


def initialize(db):
    db.execute("PRAGMA foreign_keys=ON")
    db.executescript("""
    CREATE TABLE IF NOT EXISTS reservation_state (
      venue_id TEXT NOT NULL, reservation_id TEXT NOT NULL,
      status TEXT NOT NULL CHECK(status IN ('held','confirmed','cancelled','no_show')),
      revision INTEGER NOT NULL CHECK(revision >= 0),
      PRIMARY KEY(venue_id, reservation_id));
    CREATE TABLE IF NOT EXISTS reservation_mock_outbox (
      event_key TEXT PRIMARY KEY, venue_id TEXT NOT NULL,
      reservation_id TEXT NOT NULL, revision INTEGER NOT NULL,
      event_type TEXT NOT NULL, created_at TEXT NOT NULL, payload TEXT NOT NULL,
      UNIQUE(venue_id, reservation_id, revision));
    """)


def _ids(venue_id, reservation_id):
    for value in (venue_id, reservation_id):
        if not isinstance(value, str) or not 0 < len(value) <= 100 or not value.isascii() or any(not (c.isalnum() or c in "-_") for c in value):
            raise ValueError("Invalid opaque identifier")


def register(db, venue_id, reservation_id):
    _ids(venue_id, reservation_id)
    with db:
        db.execute("INSERT INTO reservation_state VALUES (?,?,?,?)", (venue_id, reservation_id, "held", 0))


def transition(db, venue_id, reservation_id, expected_revision, new_status, *, now=None):
    """Commit reservation status and contact-free mock intent atomically."""
    _ids(venue_id, reservation_id)
    if type(expected_revision) is not int or expected_revision < 0 or new_status not in ALLOWED:
        raise ValueError("Invalid revision or status")
    timestamp = now or datetime.now(timezone.utc)
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("Timezone-aware timestamp required")
    db.execute("BEGIN IMMEDIATE")
    try:
        row = db.execute("SELECT status, revision FROM reservation_state WHERE venue_id=? AND reservation_id=?", (venue_id, reservation_id)).fetchone()
        if row is None or row[1] != expected_revision:
            raise ValueError("Unknown reservation or stale revision")
        if new_status not in ALLOWED[row[0]]:
            raise ValueError("Invalid state transition")
        revision = expected_revision + 1
        key = hashlib.sha256(json.dumps([venue_id, reservation_id, revision, new_status], separators=(",", ":")).encode()).hexdigest()
        changed = db.execute("UPDATE reservation_state SET status=?, revision=? WHERE venue_id=? AND reservation_id=? AND revision=?", (new_status, revision, venue_id, reservation_id, expected_revision))
        if changed.rowcount != 1:
            raise ValueError("Concurrent revision change")
        payload = json.dumps({"reservation_id": reservation_id, "status": new_status, "revision": revision}, separators=(",", ":"))
        db.execute("INSERT INTO reservation_mock_outbox VALUES (?,?,?,?,?,?,?)", (key, venue_id, reservation_id, revision, "reservation." + new_status, timestamp.astimezone(timezone.utc).isoformat(), payload))
        db.commit()
        return key
    except BaseException:
        db.rollback()
        raise


def queued_for_venue(db, venue_id):
    _ids(venue_id, "dummy")
    return db.execute("SELECT event_key, event_type, payload FROM reservation_mock_outbox WHERE venue_id=? ORDER BY created_at, event_key", (venue_id,)).fetchall()


class OfflineOutboxTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:", isolation_level=None)
        initialize(self.db)
        register(self.db, "venue_a", "r1")

    def tearDown(self):
        self.db.close()

    def test_atomic_success(self):
        key = transition(self.db, "venue_a", "r1", 0, "confirmed")
        self.assertEqual(len(key), 64)
        self.assertEqual(self.db.execute("SELECT status,revision FROM reservation_state").fetchone(), ("confirmed", 1))
        self.assertEqual(len(queued_for_venue(self.db, "venue_a")), 1)

    def test_stale_revision(self):
        transition(self.db, "venue_a", "r1", 0, "confirmed")
        with self.assertRaises(ValueError):
            transition(self.db, "venue_a", "r1", 0, "confirmed")
        self.assertEqual(len(queued_for_venue(self.db, "venue_a")), 1)

    def test_venue_isolation(self):
        with self.assertRaises(ValueError):
            transition(self.db, "venue_b", "r1", 0, "confirmed")
        transition(self.db, "venue_a", "r1", 0, "confirmed")
        self.assertEqual(queued_for_venue(self.db, "venue_b"), [])

    def test_invalid_transition(self):
        with self.assertRaises(ValueError):
            transition(self.db, "venue_a", "r1", 0, "no_show")
        self.assertEqual(queued_for_venue(self.db, "venue_a"), [])

    def test_rollback_if_outbox_fails(self):
        self.db.execute("CREATE TRIGGER reject_outbox BEFORE INSERT ON reservation_mock_outbox BEGIN SELECT RAISE(ABORT, 'mock failure'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            transition(self.db, "venue_a", "r1", 0, "confirmed")
        self.assertEqual(self.db.execute("SELECT status,revision FROM reservation_state").fetchone(), ("held", 0))

    def test_no_contact_details(self):
        transition(self.db, "venue_a", "r1", 0, "confirmed")
        self.assertNotIn("@", str(queued_for_venue(self.db, "venue_a")))

    def test_timezone_required(self):
        with self.assertRaises(ValueError):
            transition(self.db, "venue_a", "r1", 0, "confirmed", now=datetime(2026, 11, 16))

    def test_terminal_cancelled(self):
        transition(self.db, "venue_a", "r1", 0, "cancelled")
        with self.assertRaises(ValueError):
            transition(self.db, "venue_a", "r1", 1, "no_show")


if __name__ == "__main__":
    unittest.main()
