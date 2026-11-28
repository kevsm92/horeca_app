import unittest
from horeca.purchasing import Requisition, Status, transition


class PurchasingTests(unittest.TestCase):
    def setUp(self):
        self.req = Requisition('r1', 'venue-a', 'worker-1', 'supplier-fictional', 'SKU-1', 3, 125)

    def test_submit_and_independent_approval(self):
        submitted = transition(self.req, venue_id='venue-a', actor_id='worker-1', role='staff', action='submit')
        approved = transition(submitted, venue_id='venue-a', actor_id='manager-1', role='manager', action='approve')
        self.assertEqual((approved.status, approved.total_cents, approved.approver_id),
                         (Status.APPROVED, 375, 'manager-1'))
        self.assertEqual(self.req.status, Status.DRAFT)

    def test_cross_venue_rejected(self):
        with self.assertRaises(PermissionError):
            transition(self.req, venue_id='venue-b', actor_id='worker-1', role='staff', action='submit')

    def test_self_approval_and_unprivileged_approval_rejected(self):
        submitted = transition(self.req, venue_id='venue-a', actor_id='worker-1', role='staff', action='submit')
        for actor, role in [('worker-1', 'manager'), ('worker-2', 'staff')]:
            with self.assertRaises(PermissionError):
                transition(submitted, venue_id='venue-a', actor_id=actor, role=role, action='approve')

    def test_invalid_transitions_and_amounts(self):
        with self.assertRaises(ValueError):
            transition(self.req, venue_id='venue-a', actor_id='manager-1', role='manager', action='approve')
        for qty, price in [(0, 1), (1, -1), (True, 1), (2, 2**63)]:
            with self.assertRaises(ValueError):
                Requisition('r', 'v', 'u', 's', 'sku', qty, price)

    def test_reject_is_terminal(self):
        submitted = transition(self.req, venue_id='venue-a', actor_id='worker-1', role='staff', action='submit')
        rejected = transition(submitted, venue_id='venue-a', actor_id='manager-1', role='manager', action='reject')
        self.assertEqual(rejected.status, Status.REJECTED)
        with self.assertRaises(ValueError):
            transition(rejected, venue_id='venue-a', actor_id='manager-2', role='manager', action='approve')


if __name__ == '__main__':
    unittest.main()
