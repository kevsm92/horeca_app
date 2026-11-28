"""Offline synthetic inspection evidence: no compliance certification or authenticated API."""
from dataclasses import dataclass
from datetime import datetime

def utc(stamp):
    value = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    if value.tzinfo is None or value.utcoffset().total_seconds() != 0:
        raise ValueError("UTC timestamp required")
    return value

@dataclass(frozen=True)
class Observation:
    venue_id: str
    check_id: str
    sop_id: str
    sop_revision: int
    actor_id: str
    recorded_at: str
    result: str
    value: str | None = None
    unit: str | None = None

@dataclass(frozen=True)
class Review:
    venue_id: str
    check_id: str
    reviewer_id: str
    reviewed_at: str
    decision: str
    note: str

class InspectionReviews:
    def __init__(self):
        self.observations = {}
        self.reviews = {}

    def record(self, observation):
        if not all((observation.venue_id, observation.check_id, observation.sop_id,
                    observation.actor_id)) or observation.sop_revision < 1:
            raise ValueError("invalid observation identity")
        utc(observation.recorded_at)
        if observation.result not in ("pass", "fail", "not_performed"):
            raise ValueError("invalid result")
        if (observation.value is None) != (observation.unit is None):
            raise ValueError("value and unit required together")
        if observation.result == "not_performed" and observation.value is not None:
            raise ValueError("not performed cannot contain measurement")
        key = (observation.venue_id, observation.check_id)
        if key in self.observations:
            raise ValueError("immutable observation")
        self.observations[key] = observation
        return observation

    def review(self, *, venue_id, check_id, reviewer_id, reviewed_at, decision, note):
        key = (venue_id, check_id)
        observation = self.observations.get(key)
        if observation is None:
            raise ValueError("unknown venue-scoped observation")
        if not reviewer_id or reviewer_id == observation.actor_id:
            raise PermissionError("independent reviewer required")
        if decision not in ("verified_record", "needs_action") or not note.strip():
            raise ValueError("decision and note required")
        if observation.result != "pass" and decision == "verified_record":
            raise ValueError("failed or missing check cannot be verified")
        if utc(reviewed_at) < utc(observation.recorded_at):
            raise ValueError("review cannot predate observation")
        if key in self.reviews:
            raise ValueError("immutable review")
        review = Review(venue_id, check_id, reviewer_id, reviewed_at, decision, note)
        self.reviews[key] = review
        return review

    def history(self, *, venue_id, check_id):
        key = (venue_id, check_id)
        observation = self.observations.get(key)
        if observation is None:
            return ()
        return (observation,) + ((self.reviews[key],) if key in self.reviews else ())
