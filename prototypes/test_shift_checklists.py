import unittest
from shift_checklists import ChecklistRegistry, Template

class ChecklistTests(unittest.TestCase):
    def setUp(self):
        self.registry = ChecklistRegistry()
        self.template = Template('venue-a', 'fryer', 1, 'kitchen', 'CLOSING', 'temperature', 'Check fryer temperature', 'MEASUREMENT')
        self.kwargs = dict(venue_id='venue-a', shift_id='shift-1', staff_id='staff-1', template=self.template, station='kitchen', shift_type='CLOSING')

    def test_idempotent_assignment(self):
        self.assertIs(self.registry.assign(**self.kwargs), self.registry.assign(**self.kwargs))

    def test_cross_venue_template_rejected(self):
        with self.assertRaises(ValueError):
            self.registry.assign(**{**self.kwargs, 'venue_id': 'venue-b'})

    def test_station_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            self.registry.assign(**{**self.kwargs, 'station': 'floor'})

    def test_confirmation_cannot_replace_measurement(self):
        assignment = self.registry.assign(**self.kwargs)
        with self.assertRaises(ValueError):
            self.registry.record(assignment, venue_id='venue-a', actor_id='staff-1', action='CONFIRMED', at_utc='2026-11-24T00:00:00Z')

    def test_measurement_records_actor_and_revision(self):
        assignment = self.registry.assign(**self.kwargs)
        event = self.registry.record(assignment, venue_id='venue-a', actor_id='staff-1', action='MEASURED', at_utc='2026-11-24T00:00:00Z', value='165', unit='C')
        self.assertEqual((event.actor_id, assignment.template.revision, assignment.status), ('staff-1', 1, 'RECORDED'))
        self.assertNotEqual(assignment.status, 'VERIFIED')

    def test_wrong_staff_denied(self):
        assignment = self.registry.assign(**self.kwargs)
        with self.assertRaises(PermissionError):
            self.registry.record(assignment, venue_id='venue-a', actor_id='staff-2', action='PROBLEM_REPORTED', at_utc='2026-11-24T00:00:00Z')

    def test_problem_report_without_measurement(self):
        assignment = self.registry.assign(**self.kwargs)
        event = self.registry.record(assignment, venue_id='venue-a', actor_id='staff-1', action='PROBLEM_REPORTED', at_utc='2026-11-24T00:00:00Z')
        self.assertEqual(event.action, 'PROBLEM_REPORTED')

    def test_naive_time_denied(self):
        assignment = self.registry.assign(**self.kwargs)
        with self.assertRaises(ValueError):
            self.registry.record(assignment, venue_id='venue-a', actor_id='staff-1', action='PROBLEM_REPORTED', at_utc='2026-11-24T00:00:00')

if __name__ == '__main__':
    unittest.main()
