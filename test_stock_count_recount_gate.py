import unittest
from stock_count_recount_gate import reconcile_recount


class RecountGateTests(unittest.TestCase):
    def setUp(self):
        self.a = dict(venue_id='fictional-a', sku_id='synthetic-milk', snapshot_revision=8,
                      counted_units=20, actor_id='fictional-worker-1')
        self.b = dict(self.a, counted_units=21, actor_id='fictional-worker-2')

    def check(self, **kwargs):
        return reconcile_recount(venue_id='fictional-a', sku_id='synthetic-milk',
                                 first=self.a, second=self.b, **kwargs)

    def test_disputed(self):
        self.assertEqual(self.check()['status'], 'disputed_requires_investigation')

    def test_tolerance(self):
        self.assertEqual(self.check(tolerance_units=1)['status'], 'consistent_pending_manager_review')

    def test_no_post_or_certification(self):
        result = self.check()
        self.assertFalse(result['ledger_adjustment_posted'])
        self.assertFalse(result['certified'])

    def test_cross_venue_first_and_second(self):
        for record in (self.a, self.b):
            with self.subTest(record=record), self.assertRaises(PermissionError):
                reconcile_recount(venue_id='fictional-a', sku_id='synthetic-milk',
                                  first={**self.a, 'venue_id': 'fictional-b'} if record is self.a else self.a,
                                  second={**self.b, 'venue_id': 'fictional-b'} if record is self.b else self.b)

    def test_sku_mismatch(self):
        with self.assertRaises(ValueError):
            reconcile_recount(venue_id='fictional-a', sku_id='synthetic-milk',
                              first=self.a, second={**self.b, 'sku_id': 'other'})

    def test_same_actor(self):
        with self.assertRaisesRegex(ValueError, 'independent'):
            reconcile_recount(venue_id='fictional-a', sku_id='synthetic-milk',
                              first=self.a, second={**self.b, 'actor_id': self.a['actor_id']})

    def test_stale_revision(self):
        with self.assertRaisesRegex(ValueError, 'stale'):
            reconcile_recount(venue_id='fictional-a', sku_id='synthetic-milk',
                              first=self.a, second={**self.b, 'snapshot_revision': 9})

    def test_bad_quantities(self):
        for value in (-1, True, 2.5, '20'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                reconcile_recount(venue_id='fictional-a', sku_id='synthetic-milk',
                                  first=self.a, second={**self.b, 'counted_units': value})

    def test_invalid_tolerance(self):
        for value in (-1, True, 0.5):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.check(tolerance_units=value)

    def test_missing_actor(self):
        with self.assertRaises(ValueError):
            reconcile_recount(venue_id='fictional-a', sku_id='synthetic-milk',
                              first=self.a, second={**self.b, 'actor_id': ''})

    def test_invalid_revision(self):
        with self.assertRaises(ValueError):
            reconcile_recount(venue_id='fictional-a', sku_id='synthetic-milk',
                              first={**self.a, 'snapshot_revision': True}, second=self.b)


if __name__ == '__main__':
    unittest.main()
