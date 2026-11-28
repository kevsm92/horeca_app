import unittest
from tables_assignment_policy import Assignment, validate_assignment


class AssignmentPolicyTests(unittest.TestCase):
    def setUp(self):
        self.inventory = {('v1', 't1'): 4, ('v2', 't1'): 8}

    def test_valid(self):
        validate_assignment(Assignment('v1', 't1', 4), self.inventory, {})

    def test_other_venue_rejected(self):
        with self.assertRaisesRegex(ValueError, 'inventory'):
            validate_assignment(Assignment('v1', 't2', 2), self.inventory, {})

    def test_overcapacity_rejected(self):
        with self.assertRaisesRegex(ValueError, 'capacity exceeded'):
            validate_assignment(Assignment('v1', 't1', 5), self.inventory, {})

    def test_double_seating_rejected(self):
        with self.assertRaisesRegex(ValueError, 'occupied'):
            validate_assignment(Assignment('v1', 't1', 2), self.inventory, {('v1', 't1'): 's1'})

    def test_other_venue_occupancy_does_not_block(self):
        validate_assignment(Assignment('v1', 't1', 2), self.inventory, {('v2', 't1'): 's2'})

    def test_invalid_guests(self):
        for guests in (0, -1, True, 1.5, '2'):
            with self.subTest(guests=guests), self.assertRaises(ValueError):
                validate_assignment(Assignment('v1', 't1', guests), self.inventory, {})

    def test_invalid_identity(self):
        for venue, table in (('', 't1'), ('v1', ''), (None, 't1')):
            with self.subTest(venue=venue, table=table), self.assertRaises(ValueError):
                validate_assignment(Assignment(venue, table, 2), self.inventory, {})

    def test_invalid_inventory_capacity(self):
        with self.assertRaisesRegex(ValueError, 'invalid physical capacity'):
            validate_assignment(Assignment('v1', 't1', 2), {('v1', 't1'): True}, {})


if __name__ == '__main__':
    unittest.main()
