import unittest
from inventory_reconciliation import reconcile_events


def e(venue, event, delta, reason, ingredient="milk"):
    return dict(venue_id=venue, event_id=event, ingredient_id=ingredient, delta=delta, reason=reason)


class ReconciliationTests(unittest.TestCase):
    def test_venue_isolation_and_balances(self):
        events = [e("north", "r", 100, "receipt"), e("south", "r", 800, "receipt"),
                  e("north", "u", -40, "use"), e("north", "r2", 10, "receipt", "flour")]
        self.assertEqual(reconcile_events(events, "north"), {"flour": 10, "milk": 60})
        self.assertEqual(reconcile_events(events, "south"), {"milk": 800})

    def test_identical_retry_is_not_double_counted(self):
        receipt = e("north", "same", 25, "receipt")
        self.assertEqual(reconcile_events([receipt, dict(receipt)], "north"), {"milk": 25})

    def test_conflicting_retry_fails(self):
        with self.assertRaisesRegex(ValueError, "conflicting"):
            reconcile_events([e("north", "same", 25, "receipt"), e("north", "same", 26, "receipt")], "north")

    def test_negative_stock_fails_even_if_later_replenished(self):
        with self.assertRaisesRegex(ValueError, "negative stock"):
            reconcile_events([e("north", "use", -1, "use"), e("north", "r", 10, "receipt")], "north")

    def test_malformed_and_reason_sign_rejected(self):
        for bad in [e("north", "r", True, "receipt"), e("north", "r", -1, "receipt"),
                    e("north", "u", 1, "use"), e("north", "w", 1, "waste"),
                    e("north", "r", 1, "invalid"), e("north", "r", 0, "receipt")]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                reconcile_events([bad], "north")

    def test_foreign_venue_bad_event_is_not_exposed(self):
        self.assertEqual(reconcile_events([e("south", "bad", -10, "use")], "north"), {})


if __name__ == "__main__":
    unittest.main()
