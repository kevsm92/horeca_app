import sqlite3
import unittest
from datetime import date
from types import SimpleNamespace
from roster_publish import init_publish_schema, publish_week, published_revision, PublishConflict

MON = date(2026, 11, 30)
def actor(venue='a', role='manager', authenticated=True):
    return SimpleNamespace(venue_id=venue, role=role, authenticated=authenticated, staff_id='fictional-manager')

class PublishTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.execute('CREATE TABLE roster_versions (venue_id TEXT, week_monday TEXT, revision INTEGER, shifts_json TEXT, PRIMARY KEY(venue_id, week_monday))')
        init_publish_schema(self.db)
        self.db.execute('INSERT INTO roster_versions VALUES (?,?,?,?)', ('a', MON.isoformat(), 2, '[]'))
        self.db.commit()

    def test_publish_exact_revision_and_isolation(self):
        self.assertEqual(publish_week(self.db, principal=actor(), monday=MON, expected_revision=2), 2)
        self.assertEqual(published_revision(self.db, principal=actor(), monday=MON), 2)
        self.assertIsNone(published_revision(self.db, principal=actor('b'), monday=MON))
        with self.assertRaises(PublishConflict):
            publish_week(self.db, principal=actor('b'), monday=MON, expected_revision=2)

    def test_stale_and_missing_drafts_fail_closed(self):
        for revision in (1, 3):
            with self.assertRaises(PublishConflict):
                publish_week(self.db, principal=actor(), monday=MON, expected_revision=revision)
        self.assertIsNone(published_revision(self.db, principal=actor(), monday=MON))

    def test_auth_and_input_validation(self):
        for principal in (actor(role='staff'), actor(authenticated=False)):
            with self.assertRaises(PermissionError):
                publish_week(self.db, principal=principal, monday=MON, expected_revision=2)
        for revision in (True, 0, -1, '2'):
            with self.assertRaises(ValueError):
                publish_week(self.db, principal=actor(), monday=MON, expected_revision=revision)
        with self.assertRaises(ValueError):
            publish_week(self.db, principal=actor(), monday=date(2026,12,1), expected_revision=2)

    def test_republish_after_edit_requires_current_revision(self):
        publish_week(self.db, principal=actor(), monday=MON, expected_revision=2)
        self.db.execute('UPDATE roster_versions SET revision=3 WHERE venue_id=?', ('a',))
        self.db.commit()
        with self.assertRaises(PublishConflict):
            publish_week(self.db, principal=actor(), monday=MON, expected_revision=2)
        self.assertEqual(published_revision(self.db, principal=actor(), monday=MON), 2)
        publish_week(self.db, principal=actor(), monday=MON, expected_revision=3)
        self.assertEqual(published_revision(self.db, principal=actor(), monday=MON), 3)

if __name__ == '__main__':
    unittest.main()
