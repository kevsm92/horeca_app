import unittest
from kitchen_queue import QueueTicket
from kitchen_station_summary import summarize_station


class StationSummaryTests(unittest.TestCase):
    def test_counts_actionable_only_for_venue_and_station(self):
        rows = [QueueTicket('a', '1', 'kitchen', 'queued', 0),
                QueueTicket('a', '2', 'kitchen', 'preparing', 1),
                QueueTicket('a', '3', 'kitchen', 'ready', 2),
                QueueTicket('a', '4', 'kitchen', 'served', 3),
                QueueTicket('a', '5', 'kitchen', 'cancelled', 1),
                QueueTicket('b', '6', 'kitchen', 'ready', 0),
                QueueTicket('a', '7', 'bar', 'queued', 0)]
        self.assertEqual(summarize_station(rows, authorized_venue_id='a', station='kitchen').__dict__,
                         dict(station='kitchen', queued=1, preparing=1, ready=1, actionable=3))

    def test_empty_and_invalid_station(self):
        self.assertEqual(summarize_station([], authorized_venue_id='a', station='bar').actionable, 0)
        with self.assertRaises(ValueError):
            summarize_station([], authorized_venue_id='a', station='all')

    def test_duplicate_fails_closed(self):
        row = QueueTicket('a', '1', 'bar', 'queued', 0)
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            summarize_station([row, row], authorized_venue_id='a', station='bar')

    def test_foreign_corruption_not_exposed(self):
        row = QueueTicket('foreign', '1', 'bar', 'invalid', -1)
        self.assertEqual(summarize_station([row], authorized_venue_id='a', station='bar').actionable, 0)


if __name__ == '__main__':
    unittest.main()
