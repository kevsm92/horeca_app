import unittest

from backend.kitchen_orphan_reconciliation import RoutedOrder, TicketReference, orphan_tickets


class OrphanTicketTests(unittest.TestCase):
    def test_missing_and_voided_order_require_manual_review(self):
        orders = [RoutedOrder('v1', 'a', 'kitchen', 'accepted'),
                  RoutedOrder('v1', 'b', 'bar', 'voided')]
        tickets = [TicketReference('v1', 'a', 'kitchen', 't1'),
                   TicketReference('v1', 'b', 'bar', 't2'),
                   TicketReference('v1', 'c', 'kitchen', 't3')]
        self.assertEqual([t.ticket_id for t in orphan_tickets(orders, tickets, authorized_venue_id='v1')], ['t2', 't3'])

    def test_other_venue_does_not_authorize_order(self):
        orders = [RoutedOrder('v2', 'a', 'bar', 'accepted')]
        tickets = [TicketReference('v1', 'a', 'bar', 't1'), TicketReference('v2', 'a', 'bar', 't2')]
        self.assertEqual([t.ticket_id for t in orphan_tickets(orders, tickets, authorized_venue_id='v1')], ['t1'])

    def test_duplicate_order_fails_closed(self):
        order = RoutedOrder('v1', 'a', 'bar', 'accepted')
        with self.assertRaises(ValueError):
            orphan_tickets([order, order], [], authorized_venue_id='v1')

    def test_duplicate_ticket_fails_closed(self):
        ticket = TicketReference('v1', 'a', 'bar', 't1')
        with self.assertRaises(ValueError):
            orphan_tickets([], [ticket, ticket], authorized_venue_id='v1')

    def test_invalid_scope_and_station(self):
        with self.assertRaises(ValueError):
            orphan_tickets([], [], authorized_venue_id='')
        with self.assertRaises(ValueError):
            orphan_tickets([], [TicketReference('v1', 'a', 'dessert', 't1')], authorized_venue_id='v1')


if __name__ == '__main__':
    unittest.main()
