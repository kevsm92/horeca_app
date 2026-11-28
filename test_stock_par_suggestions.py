"""Synthetic tests for offline par-level suggestions."""
import unittest
from stock_par_suggestions import suggest_replenishment


class ParSuggestionTests(unittest.TestCase):
    def test_shortfall_after_reservations(self):
        self.assertEqual(suggest_replenishment(on_hand_milliunits=5000,
            reserved_milliunits=2000, par_milliunits=8000), 5000)

    def test_incoming_and_surplus(self):
        self.assertEqual(suggest_replenishment(on_hand_milliunits=5000,
            reserved_milliunits=1000, par_milliunits=8000, incoming_milliunits=3000), 1000)
        self.assertEqual(suggest_replenishment(on_hand_milliunits=9000,
            reserved_milliunits=0, par_milliunits=8000), 0)

    def test_invalid_amounts_rejected(self):
        base = dict(on_hand_milliunits=5000, reserved_milliunits=0,
                    par_milliunits=8000, incoming_milliunits=0)
        for field, invalid in [('on_hand_milliunits', -1), ('reserved_milliunits', 5001),
                               ('par_milliunits', True), ('incoming_milliunits', 0.5),
                               ('on_hand_milliunits', 1_000_000_000_001)]:
            with self.subTest(field=field, invalid=invalid):
                with self.assertRaises(ValueError):
                    suggest_replenishment(**{**base, field: invalid})


if __name__ == '__main__':
    unittest.main()
