import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from manager_table_kpis import table_kpis

NOW = datetime(2026, 11, 28, 5, tzinfo=timezone.utc)
MANAGER = SimpleNamespace(authenticated=True, role='manager', venue_id='fictional-a')


def row(**changes):
    return dict(id='t1', venue_id='fictional-a', capacity=4, seated_guests=2,
                occupied=True, observed_at=NOW, **changes)


class TableKpiTests(unittest.TestCase):
    def test_counts_and_tenant_isolation(self):
        other = dict(id='foreign', venue_id='fictional-b', capacity=8, seated_guests=8,
                     occupied=True, observed_at=NOW)
        result = table_kpis(principal=MANAGER, tables=[row(), other], as_of=NOW)
        self.assertEqual(result['metrics']['occupied_tables']['value'], 1)
        self.assertEqual(result['metrics']['seated_guests']['value'], 2)
        self.assertEqual(result['metrics']['physical_seats']['value'], 4)
        self.assertFalse(result['is_live'])

    def test_unavailable_not_zero(self):
        self.assertIsNone(table_kpis(principal=MANAGER, tables=None, as_of=NOW)['metrics']['occupied_tables']['value'])
        self.assertEqual(table_kpis(principal=MANAGER, tables=[], as_of=NOW)['metrics']['occupied_tables']['value'], 0)

    def test_authorization(self):
        for p in [SimpleNamespace(authenticated=False, role='manager', venue_id='fictional-a'),
                  SimpleNamespace(authenticated=True, role='staff', venue_id='fictional-a'),
                  SimpleNamespace(authenticated=True, role='manager', venue_id='')]:
            with self.assertRaises(PermissionError):
                table_kpis(principal=p, tables=[], as_of=NOW)

    def test_invalid_snapshots(self):
        cases = [dict(row(), capacity=1), dict(row(), seated_guests=-1),
                 dict(row(), occupied=False), dict(row(), observed_at=NOW + timedelta(seconds=1)),
                 dict(row(), observed_at=NOW.replace(tzinfo=None)), dict(row(), capacity=True)]
        for bad in cases:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                table_kpis(principal=MANAGER, tables=[bad], as_of=NOW)
        with self.assertRaises(ValueError):
            table_kpis(principal=MANAGER, tables=[row(), row()], as_of=NOW)


if __name__ == '__main__':
    unittest.main()
