"""Synthetic, offline regression tests for shared-schema cancellation."""
import sqlite3
import unittest
from reservation_cancel_booking_sqlite import cancel_booking, BookingCancellationConflict


class CancelBookingTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.execute('CREATE TABLE bookings (venue TEXT NOT NULL, id TEXT NOT NULL, '
                        'status TEXT NOT NULL, revision INTEGER NOT NULL, '
                        'PRIMARY KEY (venue,id))')
        self.db.executemany('INSERT INTO bookings VALUES (?,?,?,?)', [
            ('a','r','confirmed',4), ('b','r','confirmed',4),
            ('a','seated','seated',0), ('a','done','cancelled',2)])
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def state(self, venue='a', booking='r'):
        return self.db.execute('SELECT status,revision FROM bookings WHERE venue=? AND id=?',
                               (venue, booking)).fetchone()

    def test_cancel_and_preserve_other_tenant(self):
        self.assertEqual(cancel_booking(self.db, venue='a', booking_id='r', expected_revision=4), 5)
        self.assertEqual(self.state(), ('cancelled', 5))
        self.assertEqual(self.state('b'), ('confirmed', 4))

    def test_cross_tenant_cannot_cancel(self):
        with self.assertRaises(BookingCancellationConflict):
            cancel_booking(self.db, venue='c', booking_id='r', expected_revision=4)
        self.assertEqual(self.state(), ('confirmed', 4))

    def test_stale_and_repeat_rejected(self):
        with self.assertRaises(BookingCancellationConflict):
            cancel_booking(self.db, venue='a', booking_id='r', expected_revision=3)
        cancel_booking(self.db, venue='a', booking_id='r', expected_revision=4)
        with self.assertRaises(BookingCancellationConflict):
            cancel_booking(self.db, venue='a', booking_id='r', expected_revision=5)

    def test_seated_and_cancelled_not_rewritten(self):
        for booking, revision, status in [('seated',0,'seated'), ('done',2,'cancelled')]:
            with self.assertRaises(BookingCancellationConflict):
                cancel_booking(self.db, venue='a', booking_id=booking, expected_revision=revision)
            self.assertEqual(self.state('a', booking), (status,revision))

    def test_invalid_inputs_and_nested_transaction(self):
        for revision in (True, -1, '4'):
            with self.assertRaises(ValueError):
                cancel_booking(self.db, venue='a', booking_id='r', expected_revision=revision)
        with self.assertRaises(ValueError):
            cancel_booking(self.db, venue=' ', booking_id='r', expected_revision=4)
        self.db.execute('BEGIN')
        with self.assertRaises(ValueError):
            cancel_booking(self.db, venue='a', booking_id='r', expected_revision=4)
        self.db.rollback()
        self.assertEqual(self.state(), ('confirmed', 4))


if __name__ == '__main__':
    unittest.main()
