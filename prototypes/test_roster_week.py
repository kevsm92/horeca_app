import unittest
from datetime import date
from roster_week import weekly_roster, RosterAccessError

ACTOR = {'role': 'manager', 'venue_id': 'fictional-a'}
SHIFT = {'id':'s1','venue_id':'fictional-a','staff_id':'fictional-worker-1','station':'kitchen',
         'starts_at':'2026-11-29T23:00:00+01:00','ends_at':'2026-11-30T02:00:00+01:00'}

class RosterWeekTests(unittest.TestCase):
    def test_cross_midnight_boundary(self):
        result=weekly_roster(actor=ACTOR,venue_id='fictional-a',monday=date(2026,11,30),shifts=[SHIFT])
        self.assertEqual(len(result['shifts']),1)
        self.assertEqual(result['shifts'][0]['attendance'],'unknown')
    def test_tenant_isolation(self):
        result=weekly_roster(actor=ACTOR,venue_id='fictional-a',monday=date(2026,11,30),shifts=[{**SHIFT,'venue_id':'fictional-b'}])
        self.assertEqual(result['shifts'],[])
    def test_authorization(self):
        for actor in (None,{'role':'staff','venue_id':'fictional-a'},{'role':'manager','venue_id':'fictional-b'}):
            with self.assertRaises(RosterAccessError):
                weekly_roster(actor=actor,venue_id='fictional-a',monday=date(2026,11,30),shifts=[SHIFT])
    def test_invalid_week_and_naive_timestamp(self):
        with self.assertRaises(ValueError):
            weekly_roster(actor=ACTOR,venue_id='fictional-a',monday=date(2026,11,28),shifts=[])
        with self.assertRaises(ValueError):
            weekly_roster(actor=ACTOR,venue_id='fictional-a',monday=date(2026,11,30),shifts=[{**SHIFT,'starts_at':'2026-11-29T23:00:00'}])

if __name__=='__main__': unittest.main()
