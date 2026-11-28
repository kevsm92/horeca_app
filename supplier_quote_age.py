"""Offline advisory quote-age check; never automatically approves purchases."""
from datetime import datetime, timezone


def quote_age_status(recorded_at, as_of, max_age_days):
    """Return 'current', 'stale', or 'future' for canonical UTC quote timestamps.

    Stale means strictly older than the venue-configured maximum age; this is
    an advisory freshness flag, not a purchasing authorization or expiry law.
    """
    if type(max_age_days) is not int or not 0 <= max_age_days <= 3650:
        raise ValueError('max_age_days must be an integer from 0 to 3650')

    def parse(value):
        if not isinstance(value, str):
            raise ValueError('canonical UTC timestamp required')
        try:
            dt = datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
        except ValueError as exc:
            raise ValueError('canonical UTC timestamp required') from exc
        if dt.strftime('%Y-%m-%dT%H:%M:%SZ') != value:
            raise ValueError('canonical UTC timestamp required')
        return dt

    delta = parse(as_of) - parse(recorded_at)
    if delta.total_seconds() < 0:
        return 'future'
    return 'stale' if delta.total_seconds() > max_age_days * 86400 else 'current'


if __name__ == '__main__':
    import unittest

    class QuoteAgeTests(unittest.TestCase):
        def test_exact_boundary(self):
            self.assertEqual(quote_age_status('2026-11-20T12:00:00Z','2026-11-21T12:00:00Z',1),'current')
            self.assertEqual(quote_age_status('2026-11-20T11:59:59Z','2026-11-21T12:00:00Z',1),'stale')

        def test_future_quote_flagged_not_accepted(self):
            self.assertEqual(quote_age_status('2026-11-22T00:00:00Z','2026-11-21T12:00:00Z',7),'future')

        def test_zero_age(self):
            self.assertEqual(quote_age_status('2026-11-21T12:00:00Z','2026-11-21T12:00:00Z',0),'current')

        def test_rejects_invalid_policy(self):
            for n in (True,-1,3651,1.5):
                with self.assertRaises(ValueError):
                    quote_age_status('2026-11-21T12:00:00Z','2026-11-21T12:00:00Z',n)

        def test_rejects_noncanonical_and_impossible_timestamps(self):
            for bad in ('2026-02-30T12:00:00Z','2026-11-21T12:00:00+01:00','2026-11-21T1:00:00Z','2026-11-21'):
                with self.assertRaises(ValueError):
                    quote_age_status(bad,'2026-11-21T12:00:00Z',7)

        def test_timezone_independent(self):
            self.assertEqual(quote_age_status('2026-03-29T00:30:00Z','2026-03-30T00:30:00Z',1),'current')

    unittest.main()
