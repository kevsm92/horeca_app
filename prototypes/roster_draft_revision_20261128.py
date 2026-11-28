"""Offline roster draft revision guard; synthetic data only, not an HTTP API."""
import sqlite3
import unittest

def initialize(db):
    db.execute("""CREATE TABLE IF NOT EXISTS roster_draft_revision (
        venue_id TEXT NOT NULL, week_start TEXT NOT NULL,
        revision INTEGER NOT NULL DEFAULT 0,
        published INTEGER NOT NULL DEFAULT 0,
        PRIMARY KEY (venue_id, week_start))""")

def advance_draft(db, *, venue_id, week_start, expected_revision):
    """Optimistic revision guard, scoped by venue and week; published drafts immutable."""
    from datetime import date
    if not isinstance(venue_id, str) or not venue_id or type(expected_revision) is not int or expected_revision < 0:
        raise ValueError("invalid venue or revision")
    monday = date.fromisoformat(week_start)
    if monday.isoformat() != week_start or monday.weekday() != 0:
        raise ValueError("week_start must be an ISO Monday")
    with db:
        db.execute("INSERT OR IGNORE INTO roster_draft_revision (venue_id,week_start) VALUES (?,?)", (venue_id,week_start))
        cursor = db.execute("""UPDATE roster_draft_revision SET revision=revision+1
            WHERE venue_id=? AND week_start=? AND revision=? AND published=0""",
            (venue_id,week_start,expected_revision))
        if cursor.rowcount != 1:
            raise ValueError("stale revision or published roster")
    return expected_revision + 1

class RevisionTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(":memory:")
        initialize(self.db)

    def test_revision_and_venue_isolation(self):
        self.assertEqual(advance_draft(self.db,venue_id="a",week_start="2026-11-30",expected_revision=0),1)
        with self.assertRaisesRegex(ValueError,"stale"):
            advance_draft(self.db,venue_id="a",week_start="2026-11-30",expected_revision=0)
        self.assertEqual(advance_draft(self.db,venue_id="b",week_start="2026-11-30",expected_revision=0),1)

    def test_published_immutable(self):
        self.db.execute("INSERT INTO roster_draft_revision VALUES ('a','2026-11-30',2,1)")
        with self.assertRaisesRegex(ValueError,"published"):
            advance_draft(self.db,venue_id="a",week_start="2026-11-30",expected_revision=2)

    def test_invalid_week(self):
        with self.assertRaisesRegex(ValueError,"Monday"):
            advance_draft(self.db,venue_id="a",week_start="2026-12-01",expected_revision=0)

if __name__ == "__main__":
    unittest.main(verbosity=2)
