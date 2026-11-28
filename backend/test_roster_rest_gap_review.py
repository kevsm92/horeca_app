import unittest
from datetime import datetime, timedelta, timezone
from roster_rest_gap_review import rest_gap_review

BASE = datetime(2026, 11, 27, 8, tzinfo=timezone.utc)

def shift(id, start_hour, end_hour, venue='a', staff='fictional-1'):
    return {'id': id, 'venue_id': venue, 'staff_id': staff,
            'start_utc': BASE + timedelta(hours=start_hour),
            'end_utc': BASE + timedelta(hours=end_hour)}

class Tests(unittest.TestCase):
    def test_short_gap_and_no_presence_claim(self):
        result = rest_gap_review([shift('s1', 0, 8), shift('s2', 15, 20)], 'a', 600)
        self.assertEqual(result['review_flags'][0]['gap_minutes'], 420)
        self.assertFalse(result['legal_compliance_determined'])
        self.assertEqual(result['source'], 'scheduled_not_attendance')

    def test_cross_venue_and_different_staff(self):
        rows = [shift('s1', 0, 8), shift('s2', 8, 12, 'b'), shift('s3', 8, 12, staff='fictional-2')]
        self.assertEqual(rest_gap_review(rows, 'a', 600)['review_flags'], [])

    def test_overlap_and_invalid_input(self):
        self.assertEqual(rest_gap_review([shift('s1', 0, 8), shift('s2', 7, 12)], 'a', 600)['review_flags'][0]['reason'], 'overlap')
        with self.assertRaises(ValueError): rest_gap_review([], 'a', True)
        with self.assertRaises(ValueError): rest_gap_review([shift('s1', 8, 0)], 'a', 600)
        with self.assertRaises(ValueError): rest_gap_review([shift('s1', 0, 8), shift('s1', 9, 12)], 'a', 600)

if __name__ == '__main__': unittest.main()
