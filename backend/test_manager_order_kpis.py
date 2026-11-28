import unittest
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace
from manager_order_kpis import order_kpis

NOW = datetime(2026, 11, 28, 1, tzinfo=timezone.utc)
P = SimpleNamespace(authenticated=True, role='manager', venue_id='fictional-a')

class Tests(unittest.TestCase):
    def test_values_not_revenue_and_isolation(self):
        orders = [dict(id='a', venue_id='fictional-a', status='accepted', total_cents=1234, accepted_at=NOW),
                  dict(id='b', venue_id='fictional-b', status='accepted', total_cents=99999, accepted_at=NOW),
                  dict(id='c', venue_id='fictional-a', status='draft', total_cents=700, accepted_at=None)]
        result = order_kpis(principal=P, orders=orders, as_of=NOW)
        self.assertEqual(result['accepted_orders']['value'], 1)
        self.assertEqual(result['accepted_order_value']['value_cents'], 1234)
        self.assertIsNone(result['captured_revenue']['value_cents'])
        self.assertFalse(result['is_live'])

    def test_unavailable_not_zero(self):
        self.assertIsNone(order_kpis(principal=P, orders=None, as_of=NOW)['accepted_orders']['value'])
        self.assertEqual(order_kpis(principal=P, orders=[], as_of=NOW)['accepted_orders']['value'], 0)

    def test_auth_and_venue(self):
        for principal in (SimpleNamespace(authenticated=False, role='manager', venue_id='fictional-a'),
                          SimpleNamespace(authenticated=True, role='staff', venue_id='fictional-a'),
                          SimpleNamespace(authenticated=True, role='manager', venue_id='')):
            with self.assertRaises(PermissionError):
                order_kpis(principal=principal, orders=[], as_of=NOW)

    def test_bad_records_fail_closed(self):
        base = dict(id='a', venue_id='fictional-a', status='accepted', total_cents=10, accepted_at=NOW)
        for record in (dict(base, total_cents=True), dict(base, total_cents=-1),
                       dict(base, accepted_at=NOW + timedelta(seconds=1)),
                       dict(base, accepted_at=NOW.replace(tzinfo=None)), dict(base, status='paid')):
            with self.assertRaises(ValueError):
                order_kpis(principal=P, orders=[record], as_of=NOW)
        with self.assertRaises(ValueError):
            order_kpis(principal=P, orders=[base, base], as_of=NOW)

if __name__ == '__main__':
    unittest.main()
