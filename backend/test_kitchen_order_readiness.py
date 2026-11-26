import unittest
from kitchen_order_readiness import OrderStationTicket, order_readiness


class ReadinessTests(unittest.TestCase):
    def setUp(self):
        self.k = OrderStationTicket('a', 'o', 'k', 'kitchen', 'ready')
        self.b = OrderStationTicket('a', 'o', 'b', 'bar', 'preparing')

    def check(self, tickets, required=('kitchen', 'bar')):
        return order_readiness(tickets, authorized_venue_id='a', order_id='o', required_stations=required)

    def test_partial_and_full(self):
        self.assertEqual(self.check([self.k, self.b]).pending_stations, ('bar',))
        self.assertTrue(self.check([self.k, OrderStationTicket('a','o','b','bar','served')]).ready_for_handoff)

    def test_missing_station_never_ready(self):
        self.assertFalse(self.check([self.k]).ready_for_handoff)

    def test_tenant_isolation(self):
        other = OrderStationTicket('other','o','b','bar','ready')
        self.assertEqual(self.check([self.k, other]).pending_stations, ('bar',))

    def test_duplicate_and_unexpected_fail_closed(self):
        with self.assertRaises(ValueError):
            self.check([self.k, self.k])
        with self.assertRaises(ValueError):
            self.check([self.k, self.b], ('kitchen',))

    def test_cancelled_never_ready(self):
        cancelled = OrderStationTicket('a','o','b','bar','cancelled')
        self.assertFalse(self.check([self.k, cancelled]).ready_for_handoff)

    def test_invalid_requirements(self):
        with self.assertRaises(ValueError):
            self.check([self.k], ('kitchen','kitchen'))
        with self.assertRaises(ValueError):
            self.check([self.k], ())


if __name__ == '__main__':
    unittest.main()
