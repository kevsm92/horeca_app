import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from roster_draft import prepare_shift_draft


class DraftTests(unittest.TestCase):
    def setUp(self):
        self.args = dict(principal=SimpleNamespace(authenticated=True, role='manager', venue_id='v1'),
                         snapshot={'venue_id': 'v1', 'revision': 2, 'status': 'draft'}, expected_revision=2,
                         shift={'id': 'fictional-shift', 'venue_id': 'v1', 'staff_id': 'fictional-1',
                                'station': 'bar', 'start_utc': datetime(2026, 11, 27, 8, tzinfo=timezone.utc),
                                'end_utc': datetime(2026, 11, 27, 12, tzinfo=timezone.utc)},
                         staff=[{'id': 'fictional-1', 'venue_id': 'v1'}],
                         stations=[{'id': 'bar', 'venue_id': 'v1'}])

    def test_draft_proposal(self):
        result = prepare_shift_draft(**self.args)
        self.assertEqual((result['next_revision'], result['status']), (3, 'draft'))
        self.assertTrue(result['requires_atomic_compare_and_swap'])
        self.assertEqual(self.args['snapshot']['revision'], 2)

    def test_auth_tenant_and_revision(self):
        for change, error in [({'principal': SimpleNamespace(authenticated=True, role='staff', venue_id='v1')}, PermissionError),
                              ({'principal': SimpleNamespace(authenticated=False, role='manager', venue_id='v1')}, PermissionError),
                              ({'principal': SimpleNamespace(authenticated=True, role='manager', venue_id='v2')}, PermissionError),
                              ({'expected_revision': 1}, ValueError),
                              ({'snapshot': {'venue_id': 'v1', 'revision': 2, 'status': 'published'}}, ValueError)]:
            with self.subTest(change=change), self.assertRaises(error):
                prepare_shift_draft(**(self.args | change))

    def test_invalid_staff_station_and_times(self):
        for field, value in [('staff_id', 'other'), ('station', 'kitchen'),
                             ('end_utc', datetime(2026, 11, 27, 7, tzinfo=timezone.utc)),
                             ('start_utc', datetime(2026, 11, 27, 8))]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                prepare_shift_draft(**(self.args | {'shift': self.args['shift'] | {field: value}}))


if __name__ == '__main__':
    unittest.main()
