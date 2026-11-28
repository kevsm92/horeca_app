import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from roster_publish import prepare_roster_publish

class PublishTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 27, 5, tzinfo=timezone.utc)
        self.manager = SimpleNamespace(authenticated=True, role='manager', venue_id='A')
        self.shift = dict(id='s1', venue_id='A', staff_id='fictional-1',
                          start_utc=self.now, end_utc=self.now+timedelta(hours=4))
        self.args = dict(principal=self.manager, snapshot={'venue_id':'A', 'revision':2},
                         expected_revision=2, shifts=[self.shift], published_at=self.now)
    def test_success_proposes_not_persists(self):
        result = prepare_roster_publish(**self.args)
        self.assertEqual(result['next_revision'], 3)
        self.assertTrue(result['requires_atomic_compare_and_swap'])
        self.assertEqual(self.args['snapshot']['revision'], 2)
    def test_denies_staff_and_anonymous(self):
        for authenticated, role in [(True,'staff'), (False,'manager')]:
            with self.assertRaises(PermissionError):
                prepare_roster_publish(**dict(self.args, principal=SimpleNamespace(authenticated=authenticated, role=role, venue_id='A')))
    def test_tenant_mismatch(self):
        with self.assertRaises(PermissionError):
            prepare_roster_publish(**dict(self.args, snapshot={'venue_id':'B','revision':2}))
    def test_stale_revision_and_boolean(self):
        for value in [1, True]:
            with self.assertRaises(ValueError):
                prepare_roster_publish(**dict(self.args, expected_revision=value))
    def test_overlap_denied(self):
        second = dict(self.shift, id='s2', start_utc=self.now+timedelta(hours=1))
        with self.assertRaises(ValueError):
            prepare_roster_publish(**dict(self.args, shifts=[self.shift, second]))
    def test_other_venue_ignored(self):
        foreign = dict(self.shift, id='foreign', venue_id='B')
        result = prepare_roster_publish(**dict(self.args, shifts=[self.shift, foreign]))
        self.assertEqual(result['shift_ids'], ['s1'])
    def test_naive_timestamp_rejected(self):
        with self.assertRaises(ValueError):
            prepare_roster_publish(**dict(self.args, published_at=self.now.replace(tzinfo=None)))

if __name__ == '__main__':
    unittest.main()
