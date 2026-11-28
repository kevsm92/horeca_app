import unittest
from datetime import datetime, timedelta, timezone
from kitchen_ticket_age import TimedTicket, ticket_age_flags

NOW = datetime(2026, 11, 26, 5, 0, tzinfo=timezone.utc)


def ticket(id, minutes, status='queued', venue='a', station='kitchen'):
    return TimedTicket(venue, id, station, status, NOW - timedelta(minutes=minutes))


class TicketAgeTests(unittest.TestCase):
    def test_sorted_threshold_and_terminal_exclusion(self):
        result = ticket_age_flags([ticket('young', 4), ticket('old', 20),
                                   ticket('done', 40, 'served'), ticket('bar', 50, station='bar'),
                                   ticket('other', 70, venue='b')],
                                  authorized_venue_id='a', station='kitchen', now=NOW,
                                  threshold_minutes=10)
        self.assertEqual([(r.ticket_id, r.age_minutes, r.overdue) for r in result],
                         [('old', 20, True), ('young', 4, False)])

    def test_exact_boundary(self):
        self.assertTrue(ticket_age_flags([ticket('x', 10)], authorized_venue_id='a',
                                         station='kitchen', now=NOW, threshold_minutes=10)[0].overdue)

    def test_fail_closed_bad_inputs(self):
        base = dict(authorized_venue_id='a', station='kitchen', now=NOW, threshold_minutes=10)
        for rows, changes in [([ticket('x', 1), ticket('x', 2)], {}),
                              ([ticket('x', -1)], {}),
                              ([ticket('x', 1)], {'now': NOW.replace(tzinfo=None)}),
                              ([ticket('x', 1)], {'threshold_minutes': True}),
                              ([ticket('x', 1)], {'station': 'all'}),
                              ([TimedTicket('a', 'x', 'kitchen', 'queued', NOW.replace(tzinfo=None))], {})]:
            with self.subTest(rows=rows, changes=changes), self.assertRaises(ValueError):
                ticket_age_flags(rows, **(base | changes))

    def test_foreign_invalid_rows_not_disclosed(self):
        self.assertEqual(ticket_age_flags([TimedTicket('b', '', 'kitchen', 'bogus', NOW)],
                                          authorized_venue_id='a', station='kitchen', now=NOW,
                                          threshold_minutes=10), ())


if __name__ == '__main__':
    unittest.main()
