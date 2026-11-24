import unittest
from sop_acknowledgements import SOPAcknowledgements, SOPRevision


class SOPTests(unittest.TestCase):
    def setUp(self):
        self.store = SOPAcknowledgements()
        self.store.publish(SOPRevision('a', 'cold-storage', 1, 'manager', 'Cold storage SOP'))
        self.args = dict(venue_id='a', sop_id='cold-storage', revision=1,
                         actor_id='worker', staff_id='worker', at_utc='2026-11-24T01:00:00Z')

    def test_revision_specific_acknowledgement_not_inspection(self):
        event = self.store.acknowledge(**self.args)
        self.assertEqual(event.kind, 'READ_ACKNOWLEDGED')
        self.assertEqual(event.revision, 1)
        self.assertFalse(hasattr(event, 'inspection_result'))

    def test_idempotent_and_immutable_history(self):
        self.store.acknowledge(**self.args)
        self.store.acknowledge(**self.args)
        self.assertEqual(len(self.store.history(venue_id='a', staff_id='worker', actor_id='worker')), 1)
        with self.assertRaises(ValueError):
            self.store.publish(SOPRevision('a', 'cold-storage', 1, 'manager', 'Changed'))

    def test_cross_venue_revision_denied(self):
        with self.assertRaises(ValueError):
            self.store.acknowledge(**{**self.args, 'venue_id': 'b'})

    def test_other_staff_cannot_acknowledge(self):
        with self.assertRaises(PermissionError):
            self.store.acknowledge(**{**self.args, 'actor_id': 'other'})

    def test_history_is_venue_scoped_and_private(self):
        self.store.acknowledge(**self.args)
        self.assertEqual(self.store.history(venue_id='b', staff_id='worker', actor_id='worker'), ())
        with self.assertRaises(PermissionError):
            self.store.history(venue_id='a', staff_id='worker', actor_id='other')

    def test_unpublished_revision_rejected(self):
        with self.assertRaises(ValueError):
            self.store.acknowledge(**{**self.args, 'revision': 2})

    def test_naive_timestamp_rejected(self):
        with self.assertRaises(ValueError):
            self.store.acknowledge(**{**self.args, 'at_utc': '2026-11-24T01:00:00'})


if __name__ == '__main__':
    unittest.main()
