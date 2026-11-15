import unittest
from datetime import datetime, timedelta, timezone
from reservation_seating_conflict import SeatingSession, table_has_active_seating

NOW = datetime(2026, 11, 15, 6, tzinfo=timezone.utc)

class SeatingGuardTests(unittest.TestCase):
    def test_active_blocks_even_when_reservation_time_has_elapsed(self):
        self.assertTrue(table_has_active_seating('a', 't1', (SeatingSession('a','t1',2,NOW),)))

    def test_closed_session_does_not_block(self):
        self.assertFalse(table_has_active_seating('a', 't1', (SeatingSession('a','t1',2,NOW,NOW+timedelta(hours=1)),)))

    def test_cross_venue_isolation(self):
        self.assertFalse(table_has_active_seating('a','t1',(SeatingSession('b','t1',2,NOW),)))

    def test_other_table_does_not_block(self):
        self.assertFalse(table_has_active_seating('a','t1',(SeatingSession('a','t2',2,NOW),)))

    def test_invalid_same_venue_record_fails_closed(self):
        with self.assertRaises(ValueError):
            table_has_active_seating('a','t1',(SeatingSession('a','t2',0,NOW),))

    def test_naive_datetime_rejected(self):
        with self.assertRaises(ValueError):
            table_has_active_seating('a','t1',(SeatingSession('a','t1',2,NOW.replace(tzinfo=None)),))

    def test_end_before_start_rejected(self):
        with self.assertRaises(ValueError):
            table_has_active_seating('a','t1',(SeatingSession('a','t1',2,NOW,NOW-timedelta(seconds=1)),))

    def test_empty_identifiers_rejected(self):
        with self.assertRaises(ValueError):
            table_has_active_seating('', 't1', ())

if __name__ == '__main__':
    unittest.main()
