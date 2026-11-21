import unittest
from stock_count_approval_preflight import preflight_count_approval


class CountApprovalPreflightTests(unittest.TestCase):
    def setUp(self):
        self.recount = dict(venue_id='fictional-v1', sku_id='fictional-s1',
                            snapshot_revision=7, status='consistent_pending_manager_review',
                            ledger_adjustment_posted=False, certified=False)
        self.kw = dict(venue_id='fictional-v1', sku_id='fictional-s1',
                       recount=self.recount, current_revision=7,
                       manager_id='fictional-manager',
                       authorized_manager_ids={'fictional-manager'})

    def test_valid_preflight_never_approves_or_posts(self):
        result = preflight_count_approval(**self.kw)
        self.assertEqual(result['status'], 'eligible_for_separate_transactional_review')
        self.assertFalse(result['approved'])
        self.assertFalse(result['ledger_adjustment_posted'])
        self.assertFalse(result['certified'])

    def test_stale_live_revision_rejected(self):
        self.kw['current_revision'] = 8
        with self.assertRaisesRegex(ValueError, 'stale'):
            preflight_count_approval(**self.kw)

    def test_cross_venue_rejected(self):
        self.kw['venue_id'] = 'other'
        with self.assertRaises(PermissionError):
            preflight_count_approval(**self.kw)

    def test_sku_mismatch_rejected(self):
        self.kw['sku_id'] = 'other'
        with self.assertRaises(ValueError):
            preflight_count_approval(**self.kw)

    def test_unauthorized_manager_rejected(self):
        self.kw['authorized_manager_ids'] = set()
        with self.assertRaises(PermissionError):
            preflight_count_approval(**self.kw)

    def test_missing_manager_rejected(self):
        self.kw['manager_id'] = ''
        with self.assertRaises(PermissionError):
            preflight_count_approval(**self.kw)

    def test_disputed_recount_rejected(self):
        self.recount['status'] = 'disputed_requires_investigation'
        with self.assertRaises(ValueError):
            preflight_count_approval(**self.kw)

    def test_unknown_status_rejected(self):
        self.recount['status'] = 'approved'
        with self.assertRaises(ValueError):
            preflight_count_approval(**self.kw)

    def test_previously_posted_rejected(self):
        self.recount['ledger_adjustment_posted'] = True
        with self.assertRaises(ValueError):
            preflight_count_approval(**self.kw)

    def test_certified_rejected(self):
        self.recount['certified'] = True
        with self.assertRaises(ValueError):
            preflight_count_approval(**self.kw)

    def test_boolean_revision_rejected(self):
        self.kw['current_revision'] = True
        with self.assertRaises(ValueError):
            preflight_count_approval(**self.kw)

    def test_bad_manager_grant_type_rejected(self):
        self.kw['authorized_manager_ids'] = ['fictional-manager']
        with self.assertRaises(PermissionError):
            preflight_count_approval(**self.kw)


if __name__ == '__main__':
    unittest.main()
