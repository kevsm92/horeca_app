import unittest
from datetime import datetime, timezone
from kitchen_ticket import Ticket
from kitchen_transition_audit import TransitionEvent, replay_transitions

NOW = datetime(2026, 11, 26, 9, tzinfo=timezone.utc)

class AuditTests(unittest.TestCase):
    def setUp(self):
        self.ticket = Ticket('venue-a', 'ticket-1', 'kitchen')

    def event(self, source='queued', target='preparing', revision=0, venue='venue-a', ticket='ticket-1'):
        return TransitionEvent(venue, ticket, source, target, revision, NOW)

    def replay(self, events, venue='venue-a'):
        return replay_transitions(self.ticket, events, authorized_venue_id=venue)

    def test_valid_chain_and_no_mutation(self):
        final = self.replay([self.event(), self.event('preparing', 'ready', 1)])
        self.assertEqual((final.status, final.revision), ('ready', 2))
        self.assertEqual(self.ticket.status, 'queued')

    def test_missing_or_reordered_event(self):
        with self.assertRaises(ValueError):
            self.replay([self.event('preparing', 'ready', 1)])

    def test_duplicate_revision(self):
        with self.assertRaises(ValueError):
            self.replay([self.event(), self.event('preparing', 'ready', 0)])

    def test_foreign_venue_and_ticket(self):
        for event in (self.event(venue='venue-b'), self.event(ticket='ticket-2')):
            with self.assertRaises(PermissionError):
                self.replay([event])
        with self.assertRaises(PermissionError):
            self.replay([], venue='venue-b')

    def test_invalid_state_and_naive_timestamp(self):
        with self.assertRaises(ValueError):
            self.replay([self.event(target='served')])
        with self.assertRaises(ValueError):
            self.replay([TransitionEvent('venue-a', 'ticket-1', 'queued', 'preparing', 0, datetime(2026,11,26))])

    def test_empty_chain_is_initial(self):
        self.assertEqual(self.replay([]), self.ticket)

if __name__ == '__main__':
    unittest.main()
