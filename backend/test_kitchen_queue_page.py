import unittest
from kitchen_queue import QueueTicket
from kitchen_queue_page import page_station_queue


class QueuePageTests(unittest.TestCase):
    def setUp(self):
        self.tickets = [QueueTicket('v1', str(i), 'kitchen', status, 0)
                        for i, status in enumerate(['queued', 'ready', 'preparing', 'ready', 'served'])]
        self.tickets += [QueueTicket('v2', 'secret', 'kitchen', 'ready', 0),
                         QueueTicket('v1', 'bar', 'bar', 'ready', 0)]

    def test_pages_are_ordered_and_isolated(self):
        first = page_station_queue(self.tickets, authorized_venue_id='v1',
                                   station='kitchen', limit=2)
        second = page_station_queue(self.tickets, authorized_venue_id='v1',
                                    station='kitchen', limit=2, after=first.next_cursor)
        self.assertEqual([t.ticket_id for t in first.tickets + second.tickets],
                         ['1', '3', '2', '0'])
        self.assertIsNone(second.next_cursor)

    def test_empty_and_invalid_inputs(self):
        self.assertEqual(page_station_queue([], authorized_venue_id='v1',
                                            station='bar').tickets, ())
        for kwargs in ({'limit': True}, {'limit': 0}, {'limit': 101},
                       {'after': (9, 'x')}, {'after': (0, '')}, {'after': [0, 'x']}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                page_station_queue(self.tickets, authorized_venue_id='v1',
                                   station='kitchen', **kwargs)
        with self.assertRaises(ValueError):
            page_station_queue(self.tickets, authorized_venue_id='', station='kitchen')

    def test_duplicate_in_scope_fails_closed(self):
        with self.assertRaises(ValueError):
            page_station_queue(self.tickets + [self.tickets[0]],
                               authorized_venue_id='v1', station='kitchen')


if __name__ == '__main__':
    unittest.main()
