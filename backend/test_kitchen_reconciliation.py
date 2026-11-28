import unittest
from kitchen_reconciliation import RoutedOrder, TicketReference, missing_tickets


class ReconciliationTests(unittest.TestCase):
    def test_missing_and_voided_and_cross_venue(self):
        orders = [RoutedOrder('a','1','kitchen','accepted'), RoutedOrder('a','1','bar','accepted'),
                  RoutedOrder('a','2','bar','voided'), RoutedOrder('b','3','kitchen','accepted')]
        tickets = [TicketReference('a','1','kitchen','t1'), TicketReference('b','1','bar','foreign')]
        self.assertEqual(missing_tickets(orders, tickets, authorized_venue_id='a'), (('1','bar'),))

    def test_duplicates_fail_closed(self):
        order = RoutedOrder('a','1','kitchen','accepted')
        ticket = TicketReference('a','1','kitchen','t')
        with self.assertRaisesRegex(ValueError, 'duplicate routed'):
            missing_tickets([order, order], [], authorized_venue_id='a')
        with self.assertRaisesRegex(ValueError, 'duplicate ticket'):
            missing_tickets([order], [ticket, ticket], authorized_venue_id='a')

    def test_invalid_and_foreign_rows(self):
        with self.assertRaises(ValueError):
            missing_tickets([], [], authorized_venue_id='')
        with self.assertRaises(ValueError):
            missing_tickets([RoutedOrder('a','x','unknown','accepted')], [], authorized_venue_id='a')
        self.assertEqual(missing_tickets([RoutedOrder('b','x','unknown','bad')], [], authorized_venue_id='a'), ())


if __name__ == '__main__':
    unittest.main()
