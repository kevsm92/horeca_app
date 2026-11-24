"""Offline, venue-scoped SOP revision acknowledgements; never inspection evidence."""
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class SOPRevision:
    venue_id: str
    sop_id: str
    revision: int
    approved_by: str
    title: str


@dataclass(frozen=True)
class Acknowledgement:
    venue_id: str
    sop_id: str
    revision: int
    staff_id: str
    at_utc: str
    kind: str = 'READ_ACKNOWLEDGED'


class SOPAcknowledgements:
    def __init__(self):
        self._revisions = {}
        self._events = []

    def publish(self, revision: SOPRevision):
        if not all((revision.venue_id, revision.sop_id, revision.approved_by, revision.title)) or revision.revision < 1:
            raise ValueError('invalid approved revision')
        key = (revision.venue_id, revision.sop_id, revision.revision)
        if key in self._revisions:
            raise ValueError('revision already published; immutable')
        self._revisions[key] = revision

    def acknowledge(self, *, venue_id, sop_id, revision, actor_id, staff_id, at_utc):
        if not venue_id or not staff_id or actor_id != staff_id:
            raise PermissionError('only staff member may acknowledge own revision')
        if (venue_id, sop_id, revision) not in self._revisions:
            raise ValueError('unknown venue-scoped SOP revision')
        stamp = datetime.fromisoformat(at_utc.replace('Z', '+00:00'))
        if stamp.tzinfo is None or stamp.utcoffset() != timezone.utc.utcoffset(stamp):
            raise ValueError('UTC timestamp required')
        event = Acknowledgement(venue_id, sop_id, revision, staff_id, at_utc)
        if event in self._events:
            return event
        self._events.append(event)
        return event

    def history(self, *, venue_id, staff_id, actor_id, manager=False):
        if not venue_id or not staff_id or (actor_id != staff_id and not manager):
            raise PermissionError('history access denied')
        return tuple(e for e in self._events if e.venue_id == venue_id and e.staff_id == staff_id)
