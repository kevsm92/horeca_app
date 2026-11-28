import unittest
from kitchen_handoff_gate import StationHandoff, StationAck, handoff_gate


class HandoffGateTests(unittest.TestCase):
    def setUp(self):
        self.tickets = [StationHandoff('a', 'order-1', 'k1', 'kitchen', 'ready', 2),
                        StationHandoff('a', 'order-1', 'b1', 'bar', 'ready', 1)]
        self.acks = [StationAck('a', 'k1', 2, 'staff-1'), StationAck('a', 'b1', 1, 'staff-2')]

    def check(self, tickets=None, acks=None, **kwargs):
        opts = dict(authorized_venue_id='a', order_id='order-1', required_stations=('kitchen', 'bar'))
        opts.update(kwargs)
        return handoff_gate(self.tickets if tickets is None else tickets,
                            self.acks if acks is None else acks, **opts)

    def test_all_acknowledged(self):
        self.assertEqual(self.check(), ())

    def test_missing_ack(self):
        self.assertEqual(self.check(acks=self.acks[:1]), ('bar',))

    def test_stale_ack(self):
        self.assertEqual(self.check(acks=[self.acks[0], StationAck('a', 'b1', 0, 'staff')]), ('bar',))

    def test_other_venue_ack_ignored(self):
        self.assertEqual(self.check(acks=[self.acks[0], StationAck('b', 'b1', 1, 'staff')]), ('bar',))

    def test_missing_station(self):
        self.assertEqual(self.check(tickets=self.tickets[:1]), ('bar',))

    def test_served_not_acknowledgeable(self):
        self.assertEqual(self.check(tickets=[self.tickets[0], StationHandoff('a', 'order-1', 'b1', 'bar', 'served', 1)]), ('bar',))

    def test_duplicate_station_fails(self):
        with self.assertRaises(ValueError):
            self.check(tickets=self.tickets + [self.tickets[0]])

    def test_duplicate_ack_fails(self):
        with self.assertRaises(ValueError):
            self.check(acks=self.acks + [self.acks[0]])

    def test_invalid_stations_fails(self):
        with self.assertRaises(ValueError):
            self.check(required_stations=('kitchen', 'kitchen'))

    def test_cross_venue_ticket_ignored(self):
        self.assertEqual(self.check(tickets=[self.tickets[0], StationHandoff('b', 'order-1', 'b1', 'bar', 'ready', 1)]), ('bar',))


if __name__ == '__main__':
    unittest.main()
