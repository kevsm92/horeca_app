import unittest
from floorplan_accessible import render_floorplan


def tile(**overrides):
    value = dict(table_id='T1', capacity=4, guest_count=0, status='available',
                 session_id=None, x=0, y=0, can_seat=True, position_saved=False)
    value.update(overrides)
    return value


class FloorplanAccessibilityTests(unittest.TestCase):
    def test_read_only_landmarks_and_escaping(self):
        html = render_floorplan({'layout': 'provisional-grid', 'tiles': [tile(table_id='<T&1>')]})
        self.assertIn('aria-current="page"', html)
        self.assertIn('Positions are not saved', html)
        self.assertIn('&lt;T&amp;1&gt;', html)
        self.assertNotIn('<T&1>', html)
        self.assertNotIn('<button', html)

    def test_occupied_table_is_displayed_without_seat_action(self):
        html = render_floorplan({'layout': 'provisional-grid', 'tiles': [tile(status='occupied', guest_count=3, session_id='s1', can_seat=False)]})
        self.assertIn('occupied; 3 of 4 seats', html)

    def test_rejects_inconsistent_or_colliding_tiles(self):
        invalid = [tile(guest_count=1), tile(status='occupied', guest_count=2),
                   tile(status='occupied', guest_count=2, session_id='s1', can_seat=True),
                   tile(x=True), tile(position_saved=True), tile(capacity=0), tile(table_id='')]
        for bad in invalid:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                render_floorplan({'layout': 'provisional-grid', 'tiles': [bad]})
        with self.assertRaises(ValueError):
            render_floorplan({'layout': 'provisional-grid', 'tiles': [tile(), tile(table_id='T2')]})


if __name__ == '__main__':
    unittest.main()
