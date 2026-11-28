import unittest
from types import SimpleNamespace
from roster_shift_removal import prepare_shift_removal


class RemovalTests(unittest.TestCase):
    def setUp(self):
        self.principal = SimpleNamespace(authenticated=True, role='manager', venue_id='fictional-a')
        self.snapshot = {'venue_id': 'fictional-a', 'status': 'draft', 'revision': 2,
                         'shifts': [{'id': 's1', 'venue_id': 'fictional-a'}, {'id': 's2', 'venue_id': 'fictional-a'}]}

    def call(self, **kwargs):
        return prepare_shift_removal(principal=kwargs.get('principal', self.principal),
                                     snapshot=kwargs.get('snapshot', self.snapshot),
                                     expected_revision=kwargs.get('revision', 2), shift_id=kwargs.get('shift_id', 's1'))

    def test_removes_only_selected_shift_without_mutating_source(self):
        result = self.call()
        self.assertEqual([s['id'] for s in result['shifts']], ['s2'])
        self.assertEqual(len(self.snapshot['shifts']), 2)
        self.assertEqual((result['expected_revision'], result['next_revision']), (2, 3))

    def test_denies_non_manager_and_other_venue(self):
        for p in (SimpleNamespace(authenticated=False, role='manager', venue_id='fictional-a'),
                  SimpleNamespace(authenticated=True, role='staff', venue_id='fictional-a'),
                  SimpleNamespace(authenticated=True, role='manager', venue_id='fictional-b')):
            with self.assertRaises(PermissionError):
                self.call(principal=p)

    def test_stale_published_missing_and_cross_venue(self):
        for kwargs in ({'revision': 1}, {'snapshot': dict(self.snapshot, status='published')},
                       {'shift_id': 'unknown'}, {'snapshot': dict(self.snapshot, shifts=[{'id': 's1', 'venue_id': 'fictional-b'}])},
                       {'snapshot': dict(self.snapshot, shifts=[self.snapshot['shifts'][0]] * 2)}):
            with self.assertRaises(ValueError):
                self.call(**kwargs)

    def test_rejects_boolean_revision(self):
        with self.assertRaises(ValueError):
            self.call(revision=True)


if __name__ == '__main__':
    unittest.main()
