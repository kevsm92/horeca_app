import unittest
from kitchen_queue import QueueTicket, station_queue


class StationQueueTests(unittest.TestCase):
    def test_station_and_venue_isolation_and_order(self):
        rows = [QueueTicket('a','q','kitchen','queued',0),
                QueueTicket('b','foreign','kitchen','ready',0),
                QueueTicket('a','bar','bar','ready',0),
                QueueTicket('a','r','kitchen','ready',2),
                QueueTicket('a','done','kitchen','served',3),
                QueueTicket('a','p','kitchen','preparing',1)]
        self.assertEqual([t.ticket_id for t in station_queue(rows, authorized_venue_id='a', station='kitchen')], ['r','p','q'])

    def test_duplicate_requires_reconciliation(self):
        ticket = QueueTicket('a','x','bar','queued',0)
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            station_queue([ticket,ticket], authorized_venue_id='a', station='bar')

    def test_invalid_input_fails_closed(self):
        with self.assertRaises(ValueError):
            station_queue([], authorized_venue_id='', station='bar')
        with self.assertRaises(ValueError):
            station_queue([], authorized_venue_id='a', station='all')
        with self.assertRaises(ValueError):
            station_queue([QueueTicket('a','x','bar','queued',-1)], authorized_venue_id='a', station='bar')

    def test_foreign_invalid_ticket_is_not_exposed(self):
        self.assertEqual(station_queue([QueueTicket('other','x','bar','unknown',0)], authorized_venue_id='a', station='bar'), ())


if __name__ == '__main__':
    unittest.main()
