import unittest
from tables_foundation import connect, seat, close
from tables_session_history import list_session_history

class SessionHistoryTests(unittest.TestCase):
    def setUp(self):
        self.db = connect()
        self.db.executemany('INSERT INTO physical_tables VALUES (?,?,?)',
                            [('v1', 't1', 4), ('v1', 't2', 4), ('v2', 't1', 4)])
        seat(self.db, 'old', 'v1', 't1', 2)
        close(self.db, 'old', 'v1')
        seat(self.db, 'new', 'v1', 't1', 3)
        seat(self.db, 'other-table', 'v1', 't2', 1)
        seat(self.db, 'other-venue', 'v2', 't1', 4)

    def tearDown(self):
        self.db.close()

    def test_history_and_pagination(self):
        self.assertEqual(list_session_history(self.db, 'v1', 't1'), [
            {'session_id': 'new', 'guest_count': 3, 'status': 'active'},
            {'session_id': 'old', 'guest_count': 2, 'status': 'closed'}])
        self.assertEqual([r['session_id'] for r in list_session_history(self.db, 'v1', 't1', 1, 1)], ['old'])

    def test_isolation_and_missing_table(self):
        self.assertEqual([r['session_id'] for r in list_session_history(self.db, 'v2', 't1')], ['other-venue'])
        self.assertEqual(list_session_history(self.db, 'v1', 'missing'), [])

    def test_rejects_invalid_inputs(self):
        for args in [('', 't1'), ('v1', ''), ('v1', 't1', True), ('v1', 't1', 101), ('v1', 't1', 1, -1), ('v1', 't1', 1, False)]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                list_session_history(self.db, *args)

if __name__ == '__main__':
    unittest.main()
