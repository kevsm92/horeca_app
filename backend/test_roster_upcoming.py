import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from roster_upcoming import upcoming_shifts


class UpcomingTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 27, 10, tzinfo=timezone.utc)
        self.manager = SimpleNamespace(authenticated=True, role='manager', venue_id='a')

    def shift(self, sid, hours, venue='a'):
        return dict(id=sid, venue_id=venue, staff_id='fictional-1', station='bar',
                    start_utc=self.now + timedelta(hours=hours),
                    end_utc=self.now + timedelta(hours=hours + 4))

    def run_preview(self, shifts, **kwargs):
        return upcoming_shifts(principal=self.manager, shifts=shifts, as_of=self.now, **kwargs)

    def test_upcoming_order_and_no_presence_inference(self):
        result = self.run_preview([self.shift('later', 5), self.shift('first', 1), self.shift('past', -5)])
        self.assertEqual([s['id'] for s in result['shifts']], ['first', 'later'])
        self.assertTrue(all(s['attendance'] == 'unknown' for s in result['shifts']))

    def test_tenant_isolation_and_horizon(self):
        result = self.run_preview([self.shift('other', 1, 'b'), self.shift('late', 168), self.shift('ok', 167)])
        self.assertEqual([s['id'] for s in result['shifts']], ['ok'])

    def test_staff_forbidden(self):
        self.manager.role = 'staff'
        with self.assertRaises(PermissionError):
            self.run_preview([])

    def test_invalid_time_and_limit(self):
        with self.assertRaises(ValueError):
            self.run_preview([], limit=True)
        with self.assertRaises(ValueError):
            self.run_preview([dict(self.shift('bad', 1), end_utc=self.now)])

    def test_bounded_result_reports_total(self):
        result = self.run_preview([self.shift('a', 1), self.shift('b', 2)], limit=1)
        self.assertEqual((result['total'], len(result['shifts'])), (2, 1))


if __name__ == '__main__':
    unittest.main()
