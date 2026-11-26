import unittest
from kitchen_expedite import ExpediteTicket, expedite_queue


class ExpediteQueueTests(unittest.TestCase):
    def ticket(self, id, *, venue='v1', station='kitchen', status='queued',
               priority='normal', revision=0):
        return ExpediteTicket(venue, id, station, status, priority, revision)

    def test_manual_priority_and_stable_order(self):
        rows = [self.ticket('b'), self.ticket('c', priority='expedite'),
                self.ticket('a', priority='expedite', status='ready')]
        self.assertEqual([t.ticket_id for t in expedite_queue(rows, authorized_venue_id='v1', station='kitchen')], ['a', 'c', 'b'])

    def test_isolation_and_terminal_filter(self):
        rows = [self.ticket('foreign', venue='v2'), self.ticket('bar', station='bar'),
                self.ticket('done', status='served'), self.ticket('live')]
        self.assertEqual([t.ticket_id for t in expedite_queue(rows, authorized_venue_id='v1', station='kitchen')], ['live'])

    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError):
            expedite_queue([self.ticket('x'), self.ticket('x')], authorized_venue_id='v1', station='kitchen')

    def test_bad_priority_and_revision_rejected(self):
        for row in (self.ticket('x', priority='urgent'), self.ticket('x', revision=True)):
            with self.subTest(row=row), self.assertRaises(ValueError):
                expedite_queue([row], authorized_venue_id='v1', station='kitchen')

    def test_invalid_scope_rejected(self):
        with self.assertRaises(ValueError):
            expedite_queue([], authorized_venue_id='', station='kitchen')


if __name__ == '__main__':
    unittest.main()
