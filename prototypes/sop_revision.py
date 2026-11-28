"""Offline synthetic-only SOP acknowledgement model; not an inspection or certification."""
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import unittest

@dataclass(frozen=True)
class Revision:
    venue_id: str
    sop_id: str
    revision: int
    content_sha256: str
    approved_by: str

@dataclass(frozen=True)
class Acknowledgement:
    venue_id: str
    sop_id: str
    revision: int
    content_sha256: str
    staff_id: str
    acknowledged_at: str
    event_sha256: str

def acknowledge(revision: Revision, *, actor_venue: str, staff_id: str,
                at: datetime) -> Acknowledgement:
    if not revision.venue_id or actor_venue != revision.venue_id:
        raise PermissionError('venue mismatch')
    if not revision.sop_id or revision.revision < 1 or not revision.approved_by:
        raise ValueError('unapproved or invalid SOP revision')
    if len(revision.content_sha256) != 64 or any(c not in '0123456789abcdef' for c in revision.content_sha256):
        raise ValueError('invalid content digest')
    if not staff_id or not staff_id.strip():
        raise ValueError('staff identity required')
    if at.tzinfo is None or at.utcoffset() is None:
        raise ValueError('timezone-aware acknowledgement required')
    stamp = at.astimezone(timezone.utc).isoformat()
    payload = (revision.venue_id, revision.sop_id, revision.revision,
               revision.content_sha256, staff_id, stamp)
    digest = hashlib.sha256(json.dumps(payload, separators=(',', ':')).encode()).hexdigest()
    return Acknowledgement(*payload, digest)

class RevisionTests(unittest.TestCase):
    def setUp(self):
        self.rev = Revision('fictional-venue-a', 'chiller-check', 2, 'a' * 64, 'fictional-manager')
        self.now = datetime(2026, 11, 24, 18, 0, tzinfo=timezone.utc)

    def test_specific_revision_and_digest_are_preserved(self):
        event = acknowledge(self.rev, actor_venue='fictional-venue-a', staff_id='fictional-worker', at=self.now)
        self.assertEqual((event.revision, event.content_sha256), (2, 'a' * 64))
        self.assertEqual(len(event.event_sha256), 64)
        self.assertFalse(hasattr(event, 'inspection_result'))

    def test_cross_venue_denied(self):
        with self.assertRaises(PermissionError):
            acknowledge(self.rev, actor_venue='fictional-venue-b', staff_id='fictional-worker', at=self.now)

    def test_unapproved_and_naive_timestamp_denied(self):
        with self.assertRaises(ValueError):
            acknowledge(Revision('fictional-venue-a', 'x', 1, 'a' * 64, ''), actor_venue='fictional-venue-a', staff_id='fictional-worker', at=self.now)
        with self.assertRaises(ValueError):
            acknowledge(self.rev, actor_venue='fictional-venue-a', staff_id='fictional-worker', at=datetime(2026, 11, 24))

if __name__ == '__main__':
    unittest.main()
