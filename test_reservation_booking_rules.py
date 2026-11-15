import unittest
from datetime import datetime, timedelta, timezone
from reservation_booking_rules import BookingRules, validate_booking_window

H = timedelta(hours=1)
RULES = BookingRules(1, 6, H, 30 * timedelta(days=1), H, 3 * H)
NOW = datetime(2026, 11, 15, 8, tzinfo=timezone.utc)

class BookingRuleTests(unittest.TestCase):
    def check(self, **kw):
        params = dict(party=2, start=NOW + H, duration=H, now=NOW, rules=RULES)
        params.update(kw)
        return validate_booking_window(**params)

    def test_inclusive_boundaries(self):
        self.check()
        self.check(party=6, start=NOW + 30 * timedelta(days=1), duration=3 * H)

    def test_lead_and_horizon(self):
        for start in (NOW, NOW + 30 * timedelta(days=1) + timedelta(microseconds=1)):
            with self.subTest(start=start), self.assertRaises(ValueError): self.check(start=start)

    def test_party_and_duration(self):
        for party in (0, 7, True):
            with self.subTest(party=party), self.assertRaises(ValueError): self.check(party=party)
        for duration in (timedelta(0), 4 * H):
            with self.subTest(duration=duration), self.assertRaises(ValueError): self.check(duration=duration)

    def test_bad_policy_and_naive_time(self):
        with self.assertRaises(ValueError): self.check(now=NOW.replace(tzinfo=None))
        with self.assertRaises(ValueError): self.check(rules=BookingRules(1, 6, 2 * H, H, H, 3 * H))
        with self.assertRaises(ValueError): self.check(rules=BookingRules(1, 6, H, 30 * timedelta(days=1), 3 * H, H))

    def test_equivalent_offset_instant(self):
        offset = timezone(timedelta(hours=1))
        self.check(start=(NOW + H).astimezone(offset), now=NOW.astimezone(offset))

if __name__ == '__main__': unittest.main()
