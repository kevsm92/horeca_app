"""Offline stock-count variance review; never posts a stock-ledger adjustment.

Inputs must come from a trusted venue-scoped stock snapshot and an authorized
count record. This pure function does not authenticate actors or persist events.
"""


def review_count(*, venue_id, stock_venue_id, count_venue_id, sku_id,
                 stock_sku_id, count_sku_id, expected_units, counted_units,
                 snapshot_revision, count_snapshot_revision, tolerance_units=0):
    """Return a review-only discrepancy with stale snapshot protection."""
    for value in (venue_id, sku_id):
        if type(value) is not str or not value.strip():
            raise ValueError('venue and SKU identifiers required')
    if venue_id != stock_venue_id or venue_id != count_venue_id:
        raise PermissionError('cross-venue stock count denied')
    if sku_id != stock_sku_id or sku_id != count_sku_id:
        raise ValueError('count and stock SKU mismatch')
    if any(type(x) is not int or x < 0 for x in
           (expected_units, counted_units, tolerance_units)):
        raise ValueError('counts and tolerance must be nonnegative integer base units')
    if type(snapshot_revision) is not int or snapshot_revision < 0:
        raise ValueError('invalid snapshot revision')
    if type(count_snapshot_revision) is not int or count_snapshot_revision < 0:
        raise ValueError('invalid count snapshot revision')
    if snapshot_revision != count_snapshot_revision:
        raise ValueError('stale count: refresh snapshot and recount')
    variance = counted_units - expected_units
    return {'venue_id': venue_id, 'sku_id': sku_id,
            'snapshot_revision': snapshot_revision, 'variance_units': variance,
            'requires_manager_review': abs(variance) > tolerance_units,
            'status': 'review_required' if abs(variance) > tolerance_units
                      else 'within_tolerance',
            'ledger_adjustment_posted': False}


if __name__ == '__main__':
    import unittest

    class CountVarianceTests(unittest.TestCase):
        def check(self, **changes):
            p = dict(venue_id='fictional-A', stock_venue_id='fictional-A',
                     count_venue_id='fictional-A', sku_id='synthetic-flour',
                     stock_sku_id='synthetic-flour', count_sku_id='synthetic-flour',
                     expected_units=20, counted_units=17, snapshot_revision=4,
                     count_snapshot_revision=4, tolerance_units=2)
            p.update(changes)
            return review_count(**p)

        def test_shortage_requires_review(self):
            r = self.check()
            self.assertEqual((r['variance_units'], r['status']), (-3, 'review_required'))
            self.assertFalse(r['ledger_adjustment_posted'])

        def test_surplus_requires_review(self):
            self.assertEqual(self.check(counted_units=25)['variance_units'], 5)
            self.assertTrue(self.check(counted_units=25)['requires_manager_review'])

        def test_exact_tolerance_does_not_require_review(self):
            self.assertEqual(self.check(counted_units=18)['status'], 'within_tolerance')

        def test_cross_venue_denied_for_both_records(self):
            for field in ('stock_venue_id', 'count_venue_id'):
                with self.subTest(field=field), self.assertRaises(PermissionError):
                    self.check(**{field: 'fictional-B'})

        def test_mismatched_sku_denied(self):
            for field in ('stock_sku_id', 'count_sku_id'):
                with self.subTest(field=field), self.assertRaises(ValueError):
                    self.check(**{field: 'synthetic-other'})

        def test_stale_snapshot_denied(self):
            with self.assertRaisesRegex(ValueError, 'stale'):
                self.check(count_snapshot_revision=3)

        def test_bad_quantity_types_denied(self):
            for field, value in [('expected_units', True), ('counted_units', -1),
                                 ('tolerance_units', 1.5)]:
                with self.subTest(field=field), self.assertRaises(ValueError):
                    self.check(**{field: value})

        def test_invalid_revision_denied(self):
            with self.assertRaises(ValueError):
                self.check(snapshot_revision=-1)

        def test_missing_ids_denied(self):
            with self.assertRaises(ValueError):
                self.check(sku_id=' ')

        def test_exact_count_no_write(self):
            r = self.check(counted_units=20)
            self.assertEqual(r['variance_units'], 0)
            self.assertFalse(r['ledger_adjustment_posted'])

    unittest.main(verbosity=2)
