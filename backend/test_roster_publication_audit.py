import sqlite3
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from roster_publication_audit import initialize, record_publication, list_publications


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        initialize(self.db)
        self.manager = SimpleNamespace(authenticated=True, role='manager', venue_id='A', staff_id='fictional-manager')
        self.kw = dict(principal=self.manager, week_start='2026-11-23', revision=1,
                       published_at=datetime(2026, 11, 27, 17, tzinfo=timezone.utc), shift_ids=['s1'])

    def tearDown(self):
        self.db.close()

    def test_receipt_and_duplicate(self):
        self.assertEqual(record_publication(self.db, **self.kw), 1)
        self.assertEqual(list_publications(self.db, principal=self.manager, week_start='2026-11-23')[0]['shift_ids'], ['s1'])
        with self.assertRaises(sqlite3.IntegrityError):
            record_publication(self.db, **self.kw)

    def test_venue_and_rbac(self):
        record_publication(self.db, **self.kw)
        other = SimpleNamespace(authenticated=True, role='manager', venue_id='B', staff_id='fictional-other')
        self.assertEqual(list_publications(self.db, principal=other, week_start='2026-11-23'), [])
        with self.assertRaises(PermissionError):
            record_publication(self.db, **dict(self.kw, principal=SimpleNamespace(authenticated=True, role='staff', venue_id='A')))

    def test_immutable(self):
        record_publication(self.db, **self.kw)
        for statement in ['UPDATE roster_publication_receipts SET actor_id="x"', 'DELETE FROM roster_publication_receipts']:
            with self.assertRaises(sqlite3.IntegrityError):
                self.db.execute(statement)

    def test_invalid(self):
        for change in [dict(revision=True), dict(week_start='2026-11-24'), dict(shift_ids=['s1','s1']), dict(published_at=datetime(2026, 11, 27))]:
            with self.assertRaises(ValueError):
                record_publication(self.db, **dict(self.kw, **change))


if __name__ == '__main__':
    unittest.main()
