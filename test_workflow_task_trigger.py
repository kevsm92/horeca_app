import unittest
from workflow_task_trigger import task_created_trigger

class TriggerTests(unittest.TestCase):
    def test_high_priority_creates_review_intent(self):
        self.assertEqual(task_created_trigger('task.created', {'task_id': 'fictional-1', 'priority': 'high'}),
                         {'kind': 'manager_review_required', 'task_id': 'fictional-1',
                          'reason': 'priority_escalation', 'requires_human_review': True})

    def test_normal_and_unrelated_events_are_noops(self):
        self.assertIsNone(task_created_trigger('task.created', {'task_id': 'x', 'priority': 'normal'}))
        self.assertIsNone(task_created_trigger('stock.changed', {}))

    def test_rejects_bad_payload(self):
        for value in (None, {}, {'task_id': 'x', 'priority': 'invalid'},
                      {'task_id': ' ', 'priority': 'high'}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                task_created_trigger('task.created', value)

if __name__ == '__main__':
    unittest.main()
