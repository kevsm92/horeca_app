"""Synthetic regression checks for KDS void review projection."""
import unittest
from backend.kitchen_void_review import VoidOrder, StationTicket, void_review_queue


class VoidReviewTests(unittest.TestCase):
    def test_flags_only_active_voided_tickets(self):
        orders = [VoidOrder('a', '1', 'voided'), VoidOrder('a', '2', 'accepted')]
        tickets = [StationTicket('a', '1', 'k1', 'kitchen', 'preparing'),
                   StationTicket('a', '1', 'b1', 'bar', 'cancelled'),
                   StationTicket('a', '2', 'k2', 'kitchen', 'queued')]
        self.assertEqual(void_review_queue(orders, tickets, authorized_venue_id='a'), (tickets[0],))
        self.assertEqual(tickets[0].status, 'preparing')

    def test_cross_venue_data_is_not_exposed(self):
        orders = [VoidOrder('b', '1', 'voided')]
        tickets = [StationTicket('b', '1', 'other-venue-ticket', 'bar', 'ready')]
        self.assertEqual(void_review_queue(orders, tickets, authorized_venue_id='a'), ())

    def test_rejects_duplicate_and_orphan(self):
        o = VoidOrder('a', '1', 'voided')
        t = StationTicket('a', '1', 'k1', 'kitchen', 'queued')
        with self.assertRaises(ValueError):
            void_review_queue([o, o], [t], authorized_venue_id='a')
        with self.assertRaises(ValueError):
            void_review_queue([o], [t, t], authorized_venue_id='a')
        with self.assertRaises(ValueError):
            void_review_queue([], [t], authorized_venue_id='a')

    def test_rejects_invalid_status_and_missing_scope(self):
        with self.assertRaises(ValueError):
            void_review_queue([], [], authorized_venue_id='')
        with self.assertRaises(ValueError):
            void_review_queue([VoidOrder('a', '1', 'unknown')], [], authorized_venue_id='a')


if __name__ == '__main__':
    unittest.main()
