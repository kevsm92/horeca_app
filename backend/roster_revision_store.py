"""Offline SQLite CAS store for fictional weekly roster snapshots.

The caller must enforce authenticated manager/owner RBAC and derive venue_id
from its trusted session. This module is not an HTTP endpoint.
"""
import json
import sqlite3
from datetime import date


def initialize(db):
    db.execute("""CREATE TABLE IF NOT EXISTS roster_snapshots (
        venue_id TEXT NOT NULL, week_start TEXT NOT NULL,
        revision INTEGER NOT NULL CHECK(revision >= 0),
        payload TEXT NOT NULL, PRIMARY KEY (venue_id, week_start))""")


def _validate(venue_id, week_start, payload):
    if not isinstance(venue_id, str) or not venue_id.strip():
        raise ValueError("venue required")
    try:
        week = date.fromisoformat(week_start)
    except (TypeError, ValueError):
        raise ValueError("invalid week_start") from None
    if week.weekday() != 0 or week.isoformat() != week_start:
        raise ValueError("canonical Monday required")
    if not isinstance(payload, dict) or payload.get("venue_id") != venue_id or payload.get("status") not in ("draft", "published"):
        raise ValueError("cross-venue or invalid payload")


def create_snapshot(db, *, venue_id, week_start, payload):
    _validate(venue_id, week_start, payload)
    with db:
        db.execute("INSERT INTO roster_snapshots VALUES (?, ?, 0, ?)",
                   (venue_id, week_start, json.dumps(payload, sort_keys=True)))
    return 0


def read_snapshot(db, *, venue_id, week_start):
    row = db.execute("SELECT revision, payload FROM roster_snapshots WHERE venue_id=? AND week_start=?",
                     (venue_id, week_start)).fetchone()
    return None if row is None else {"revision": row[0], "payload": json.loads(row[1])}


def compare_and_swap(db, *, venue_id, week_start, expected_revision, payload):
    _validate(venue_id, week_start, payload)
    if type(expected_revision) is not int or expected_revision < 0:
        raise ValueError("invalid revision")
    with db:
        cursor = db.execute(
            "UPDATE roster_snapshots SET revision=revision+1, payload=? "
            "WHERE venue_id=? AND week_start=? AND revision=?",
            (json.dumps(payload, sort_keys=True), venue_id, week_start, expected_revision))
        if cursor.rowcount != 1:
            raise ValueError("missing or stale snapshot")
    return expected_revision + 1


if __name__ == "__main__":
    import unittest

    class Tests(unittest.TestCase):
        def setUp(self):
            self.db = sqlite3.connect(":memory:")
            initialize(self.db)
            self.p = {"venue_id": "fictional-a", "status": "draft", "shifts": []}
            create_snapshot(self.db, venue_id="fictional-a", week_start="2026-11-23", payload=self.p)

        def tearDown(self):
            self.db.close()

        def test_cas_and_stale(self):
            self.assertEqual(compare_and_swap(self.db, venue_id="fictional-a", week_start="2026-11-23", expected_revision=0, payload=self.p), 1)
            with self.assertRaises(ValueError):
                compare_and_swap(self.db, venue_id="fictional-a", week_start="2026-11-23", expected_revision=0, payload=self.p)
            self.assertEqual(read_snapshot(self.db, venue_id="fictional-a", week_start="2026-11-23")["revision"], 1)

        def test_tenant_isolation(self):
            self.assertIsNone(read_snapshot(self.db, venue_id="fictional-b", week_start="2026-11-23"))
            with self.assertRaises(ValueError):
                compare_and_swap(self.db, venue_id="fictional-b", week_start="2026-11-23", expected_revision=0, payload=self.p)

        def test_duplicate(self):
            with self.assertRaises(sqlite3.IntegrityError):
                create_snapshot(self.db, venue_id="fictional-a", week_start="2026-11-23", payload=self.p)

        def test_invalid_input(self):
            with self.assertRaises(ValueError):
                create_snapshot(self.db, venue_id="fictional-a", week_start="2026-11-24", payload=self.p)
            with self.assertRaises(ValueError):
                compare_and_swap(self.db, venue_id="fictional-a", week_start="2026-11-23", expected_revision=True, payload=self.p)
            with self.assertRaises(ValueError):
                create_snapshot(self.db, venue_id="fictional-b", week_start="2026-11-23", payload=self.p)

    unittest.main()
