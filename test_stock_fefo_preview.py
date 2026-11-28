import unittest
from datetime import datetime, timedelta, timezone
from stock_fefo_preview import preview_fefo

NOW = datetime(2026, 11, 20, 10, tzinfo=timezone.utc)

def batch(identifier, units, days=3, **kw):
    return dict(id=identifier, units=units, manufacturer_use_by=NOW + timedelta(days=days), **kw)

class FefoTests(unittest.TestCase):
    def preview(self, batches, requested_units=5):
        return preview_fefo(now=NOW, requested_units=requested_units, batches=batches)

    def test_earliest_deadline_first(self):
        result = self.preview([batch('late', 8, 5), batch('early', 3, 1)])
        self.assertEqual([(x['batch_id'], x['units']) for x in result['allocations']], [('early', 3), ('late', 2)])
        self.assertFalse(result['posted'])
        self.assertFalse(result['reserved'])
    def test_opening_deadline_wins(self):
        opened = NOW - timedelta(days=1)
        result = self.preview([batch('original', 10, 2), batch('opened', 10, 8, opened_at=opened, post_open_discard=NOW + timedelta(hours=1))])
        self.assertEqual(result['allocations'][0]['batch_id'], 'opened')
    def test_expired_excluded(self):
        result = self.preview([batch('expired', 10, -1), batch('valid', 2)], 4)
        self.assertEqual(result['unfulfilled_units'], 2)
        self.assertEqual(result['excluded_batches'][0]['status'], 'expired')
        self.assertTrue(result['requires_manual_review'])
    def test_missing_opening_rule_excluded(self):
        result = self.preview([batch('opened', 10, opened_at=NOW - timedelta(hours=1))])
        self.assertEqual(result['allocations'], [])
        self.assertEqual(result['excluded_batches'][0]['status'], 'missing_post_open_rule')
    def test_future_opening_excluded(self):
        result = self.preview([batch('future', 10, opened_at=NOW + timedelta(hours=1))])
        self.assertEqual(result['excluded_batches'][0]['status'], 'untrusted_opening')
    def test_insufficient_inventory_flagged(self):
        result = self.preview([batch('one', 1)])
        self.assertEqual(result['unfulfilled_units'], 4)
        self.assertTrue(result['requires_manual_review'])
    def test_duplicate_ids_rejected(self):
        with self.assertRaises(ValueError):
            self.preview([batch('same', 2), batch('same', 4)])
    def test_invalid_quantities_rejected(self):
        for quantity in (True, 0, -1, 1.5):
            with self.subTest(quantity=quantity), self.assertRaises(ValueError):
                self.preview([], requested_units=quantity)
    def test_invalid_batch_units_rejected(self):
        with self.assertRaises(ValueError):
            self.preview([batch('bad', True)])
    def test_naive_time_rejected(self):
        with self.assertRaises(ValueError):
            preview_fefo(now=datetime(2026, 11, 20), requested_units=1, batches=[])
    def test_input_not_mutated(self):
        items = [batch('one', 6)]
        before = [dict(item) for item in items]
        self.preview(items)
        self.assertEqual(items, before)

if __name__ == '__main__':
    unittest.main()
