import sqlite3
import unittest
from datetime import date, datetime, timezone
from prototypes.weekly_roster import init_schema, add_shift
from roster_manager_read import Principal, manager_week_snapshot


class ManagerReadTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        init_schema(self.db)
        self.db.executemany('INSERT INTO roster_staff VALUES (?,?,?,?)', [
            ('venue-a', 'a1', 'Fictional Ada', 'Kitchen'),
            ('venue-b', 'b1', 'Fictional Bea', 'Bar')])
        add_shift(self.db, venue_id='venue-a', shift_id='sa', staff_id='a1',
                  start=datetime(2026, 11, 30, 9, tzinfo=timezone.utc),
                  end=datetime(2026, 11, 30, 17, tzinfo=timezone.utc))

    def read(self, venue='venue-a', role='manager', authenticated=True):
        return manager_week_snapshot(self.db, principal=Principal('mgr', venue, role, authenticated),
                                     monday=date(2026, 11, 30))

    def test_manager_sees_only_own_venue(self):
        self.assertEqual([s['id'] for s in self.read()['staff']], ['a1'])
        self.assertEqual([s['id'] for s in self.read('venue-b')['staff']], ['b1'])

    def test_schedule_does_not_claim_presence(self):
        self.assertEqual(self.read()['staff'][0]['shifts'][0]['attendance'], 'unknown')

    def test_denied_unauthenticated_and_staff(self):
        for role, authenticated in [('manager', False), ('staff', True), ('', True)]:
            with self.subTest(role=role, authenticated=authenticated):
                with self.assertRaises(PermissionError):
                    self.read(role=role, authenticated=authenticated)

    def test_denied_missing_venue(self):
        with self.assertRaises(PermissionError):
            self.read(venue='')


if __name__ == '__main__':
    unittest.main()
