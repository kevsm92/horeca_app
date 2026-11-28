import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from manager_kitchen_hourly_series import kitchen_hourly_series

NOW = datetime(2026, 11, 28, 12, 30, tzinfo=timezone.utc)
P = SimpleNamespace(authenticated=True, role='manager', venue_id='fictional-a')

class Tests(unittest.TestCase):
    def test_buckets_and_isolation(self):
        tickets = [dict(id='one', venue_id='fictional-a', created_at=NOW),
                   dict(id='two', venue_id='fictional-a', created_at=NOW - timedelta(hours=1)),
                   dict(id='other', venue_id='fictional-b', created_at=NOW)]
        result = kitchen_hourly_series(principal=P, tickets=tickets, as_of=NOW, hours=2)
        self.assertEqual([x['ticket_count'] for x in result['series']], [1, 1])
        self.assertFalse(result['is_live'])

    def test_missing_source_not_zero(self):
        self.assertIsNone(kitchen_hourly_series(principal=P, tickets=None, as_of=NOW)['series'][0]['ticket_count'])
        self.assertEqual(kitchen_hourly_series(principal=P, tickets=[], as_of=NOW)['series'][0]['ticket_count'], 0)

    def test_rejects_unauthorized_and_invalid(self):
        with self.assertRaises(PermissionError):
            kitchen_hourly_series(principal=SimpleNamespace(authenticated=True, role='staff', venue_id='fictional-a'), tickets=[], as_of=NOW)
        with self.assertRaises(ValueError):
            kitchen_hourly_series(principal=P, tickets=[], as_of=NOW, hours=True)
        for t in (NOW + timedelta(seconds=1), NOW.replace(tzinfo=None)):
            with self.assertRaises(ValueError):
                kitchen_hourly_series(principal=P, tickets=[dict(id='x', venue_id='fictional-a', created_at=t)], as_of=NOW)
        with self.assertRaises(ValueError):
            kitchen_hourly_series(principal=P, tickets=[dict(id='x', venue_id='fictional-a', created_at=NOW)] * 2, as_of=NOW)

if __name__ == '__main__':
    unittest.main()
