"""Offline-only reservation notification intent outbox. No delivery transport."""
from dataclasses import dataclass, replace
from hashlib import sha256
import json
import unittest

ALLOWED = frozenset({'reservation_confirmed', 'reservation_cancelled', 'waitlist_offer'})

@dataclass(frozen=True)
class Intent:
    venue_id: str
    reservation_id: str
    event_type: str
    revision: int
    template_key: str
    idempotency_key: str

def make_intent(venue_id: str, reservation_id: str, event_type: str, revision: int) -> Intent:
    """Create a non-deliverable, contact-free, deterministic notification intent."""
    if any(type(v) is not str or not v or len(v) > 128 or not v.isascii() or
           not all(c.isalnum() or c in '-_' for c in v)
           for v in (venue_id, reservation_id)):
        raise ValueError('Invalid venue or reservation identifier')
    if event_type not in ALLOWED or type(revision) is not int or revision < 1:
        raise ValueError('Invalid event type or revision')
    canonical = json.dumps([venue_id, reservation_id, event_type, revision], separators=(',', ':'))
    return Intent(venue_id, reservation_id, event_type, revision, event_type,
                  sha256(canonical.encode('ascii')).hexdigest())

class MockOutbox:
    """In-memory, venue-scoped and idempotent. No guest contact or transport."""
    def __init__(self):
        self._intents: dict[str, Intent] = {}

    def enqueue(self, intent: Intent) -> bool:
        if not isinstance(intent, Intent) or intent != make_intent(
            intent.venue_id, intent.reservation_id, intent.event_type, intent.revision
        ):
            raise ValueError('Untrusted intent')
        if intent.idempotency_key in self._intents:
            return False
        self._intents[intent.idempotency_key] = intent
        return True

    def for_venue(self, venue_id: str) -> tuple[Intent, ...]:
        if type(venue_id) is not str or not venue_id:
            raise ValueError('Invalid venue')
        return tuple(x for x in self._intents.values() if x.venue_id == venue_id)

class MockOutboxTests(unittest.TestCase):
    def test_deduplication(self):
        box=MockOutbox(); item=make_intent('venue-a','res-1','reservation_confirmed',1)
        self.assertTrue(box.enqueue(item)); self.assertFalse(box.enqueue(item))
        self.assertEqual(len(box.for_venue('venue-a')),1)

    def test_revision_is_new_intent(self):
        box=MockOutbox()
        self.assertTrue(box.enqueue(make_intent('venue-a','res-1','reservation_cancelled',1)))
        self.assertTrue(box.enqueue(make_intent('venue-a','res-1','reservation_cancelled',2)))

    def test_venue_isolation(self):
        box=MockOutbox()
        for venue in ('venue-a','venue-b'):
            box.enqueue(make_intent(venue,'res-1','waitlist_offer',1))
        self.assertEqual(len(box.for_venue('venue-a')),1)
        self.assertEqual(box.for_venue('venue-a')[0].venue_id,'venue-a')

    def test_no_contact_data(self):
        self.assertEqual(set(make_intent('v','r','waitlist_offer',1).__dict__),
                         {'venue_id','reservation_id','event_type','revision','template_key','idempotency_key'})

    def test_invalid_input_fails_closed(self):
        for args in [('v','r','unknown',1),('v','r','waitlist_offer',0),
                     ('v','r','waitlist_offer',True),('v','bad@example.com','waitlist_offer',1)]:
            with self.assertRaises(ValueError): make_intent(*args)

    def test_tampered_intent_rejected(self):
        box=MockOutbox(); i=make_intent('v','r','waitlist_offer',1)
        with self.assertRaises(ValueError): box.enqueue(replace(i,idempotency_key='fake'))

if __name__ == '__main__':
    unittest.main()
