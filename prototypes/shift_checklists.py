"""Offline shift checklist domain. Recording a check is not safety verification."""
from dataclasses import dataclass, field
from datetime import datetime

@dataclass(frozen=True)
class Template:
    venue_id: str
    template_id: str
    revision: int
    station: str
    shift_type: str
    item_id: str
    title: str
    evidence_kind: str

@dataclass(frozen=True)
class AuditEvent:
    actor_id: str
    action: str
    at_utc: str
    value: str | None = None
    unit: str | None = None

@dataclass
class Assignment:
    venue_id: str
    shift_id: str
    staff_id: str
    template: Template
    events: list[AuditEvent] = field(default_factory=list)

    @property
    def status(self):
        return 'RECORDED' if self.events else 'PENDING'

class ChecklistRegistry:
    def __init__(self):
        self._assignments = {}

    def assign(self, *, venue_id, shift_id, staff_id, template, station, shift_type):
        if not all((venue_id, shift_id, staff_id)) or template.venue_id != venue_id:
            raise ValueError('invalid venue or assignment identity')
        if template.station != station or template.shift_type != shift_type or template.revision < 1:
            raise ValueError('template does not match published shift')
        key = (venue_id, shift_id, staff_id, template.template_id, template.revision, template.item_id)
        if key not in self._assignments:
            self._assignments[key] = Assignment(venue_id, shift_id, staff_id, template)
        return self._assignments[key]

    def record(self, assignment, *, venue_id, actor_id, action, at_utc, value=None, unit=None):
        if assignment.venue_id != venue_id or assignment.staff_id != actor_id:
            raise PermissionError('assignment not accessible to actor')
        if action not in ('CONFIRMED', 'MEASURED', 'PROBLEM_REPORTED'):
            raise ValueError('unsupported action')
        if action == 'CONFIRMED' and assignment.template.evidence_kind != 'CONFIRMATION':
            raise ValueError('measurement cannot be replaced by confirmation')
        if action == 'MEASURED' and (assignment.template.evidence_kind != 'MEASUREMENT' or not value or not unit):
            raise ValueError('measurement requires a value and unit')
        if action != 'MEASURED' and (value is not None or unit is not None):
            raise ValueError('unexpected measurement data')
        timestamp = datetime.fromisoformat(at_utc.replace('Z', '+00:00'))
        if timestamp.tzinfo is None or timestamp.utcoffset().total_seconds() != 0:
            raise ValueError('UTC timestamp required')
        event = AuditEvent(actor_id, action, at_utc, value, unit)
        assignment.events.append(event)
        return event
