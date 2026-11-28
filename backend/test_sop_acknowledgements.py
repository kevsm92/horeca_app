import sqlite3
import unittest

from backend.sop_revisions import approve_revision
from backend.sop_acknowledgements import initialize, acknowledge, list_acknowledgements


class AcknowledgementTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        initialize(self.db)
        approve_revision(
            self.db, venue_id="fictional-a", sop_id="chiller",
            author_id="writer", approver_id="reviewer", station="kitchen",
            content="Synthetic chiller SOP", expected_previous_revision=0,
        )
        self.data = dict(
            venue_id="fictional-a", sop_id="chiller", revision=1,
            actor_id="fictional-worker", acknowledged_at="2026-11-24T12:00:00+01:00",
        )

    def test_revision_scoped_and_duplicate_rejected(self):
        acknowledge(self.db, **self.data)
        self.assertEqual(len(list_acknowledgements(
            self.db, venue_id="fictional-a", sop_id="chiller", revision=1)), 1)
        with self.assertRaises(sqlite3.IntegrityError):
            acknowledge(self.db, **self.data)
        self.assertEqual(list_acknowledgements(
            self.db, venue_id="fictional-b", sop_id="chiller", revision=1), [])

    def test_unapproved_or_other_venue_revision_rejected(self):
        for changes in ({"revision": 2}, {"venue_id": "fictional-b"}):
            with self.assertRaises(sqlite3.IntegrityError):
                acknowledge(self.db, **{**self.data, **changes})
        self.assertEqual(self.db.execute(
            "SELECT COUNT(*) FROM sop_acknowledgements").fetchone()[0], 0)

    def test_timezone_and_identity_validation(self):
        for changes in ({"acknowledged_at": "2026-11-24T12:00:00"},
                        {"actor_id": " "}, {"revision": True}):
            with self.assertRaises(ValueError):
                acknowledge(self.db, **{**self.data, **changes})

    def test_immutable_and_not_a_physical_check(self):
        acknowledge(self.db, **self.data)
        for sql in ("UPDATE sop_acknowledgements SET actor_id='other'",
                    "DELETE FROM sop_acknowledgements"):
            with self.assertRaises(sqlite3.IntegrityError):
                self.db.execute(sql)
        columns = {row[1] for row in self.db.execute(
            "PRAGMA table_info(sop_acknowledgements)")}
        self.assertFalse({"result", "measured_value", "manager_verified"} & columns)


if __name__ == "__main__":
    unittest.main()
