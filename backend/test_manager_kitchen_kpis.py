import unittest
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace
from manager_kitchen_kpis import kitchen_kpis

NOW = datetime(2026, 11, 28, 2, tzinfo=timezone.utc)
P = SimpleNamespace(authenticated=True, role='manager', venue_id='fictional-a')


class KitchenKpiTests(unittest.TestCase):
    def test_open_states_and_tenant_isolation(self):
        rows = [dict(id=str(i), venue_id='fictional-a', status=state, created_at=NOW)
                for i, state in enumerate(('queued', 'preparing', 'ready', 'handed_off', 'voided'))]
        rows.append(dict(id='secret', venue_id='fictional-b', status='queued', created_at=NOW))
        result = kitchen_kpis(principal=P, tickets=rows, as_of=NOW)
        self.assertEqual(result['open_kitchen_tickets']['value'], 3)
        self.assertFalse(result['is_live'])

    def test_missing_source_is_not_zero(self):
        self.assertIsNone(kitchen_kpis(principal=P, tickets=None, as_of=NOW)['open_kitchen_tickets']['value'])
        self.assertEqual(kitchen_kpis(principal=P, tickets=[], as_of=NOW)['open_kitchen_tickets']['value'], 0)

    def test_auth_and_invalid_records(self):
        for principal in (SimpleNamespace(authenticated=False, role='manager', venue_id='fictional-a'),
                          SimpleNamespace(authenticated=True, role='staff', venue_id='fictional-a'),
                          SimpleNamespace(authenticated=True, role='manager', venue_id='')):
            with self.assertRaises(PermissionError):
                kitchen_kpis(principal=principal, tickets=[], as_of=NOW)
        valid = dict(id='t', venue_id='fictional-a', status='queued', created_at=NOW)
        for bad in (dict(valid, status='unknown'), dict(valid, created_at=NOW + timedelta(seconds=1)),
                    dict(valid, created_at=NOW.replace(tzinfo=None)), dict(valid, id='')):
            with self.assertRaises(ValueError):
                kitchen_kpis(principal=P, tickets=[bad], as_of=NOW)
        with self.assertRaises(ValueError):
            kitchen_kpis(principal=P, tickets=[valid, valid], as_of=NOW)


if __name__ == '__main__':
    unittest.main()
