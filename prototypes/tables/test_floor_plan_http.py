import json
import sqlite3
import unittest
from floor_plan_http import initialize_floor_plan, make_floor_plan_app

class FloorPlanHTTPTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(':memory:')
        self.db.execute('PRAGMA foreign_keys=ON')
        initialize_floor_plan(self.db)
        self.db.executemany('INSERT INTO floor_physical_tables VALUES (?,?,?,?)',
                            [('A','T1',4,2),('B','T1',6,5)])
        self.db.executemany('INSERT INTO floor_layout_meta VALUES (?,?)',[('A',3),('B',8)])
        self.db.executemany('INSERT INTO floor_placements VALUES (?,?,?,?)',
                            [('A','T1',25,30),('B','T1',70,75)])
    def tearDown(self):
        self.db.close()
    def call(self, resolver, method='GET', query='', path='/api/v1/floor-plan'):
        status=[]
        app=make_floor_plan_app(self.db,resolver)
        body=b''.join(app({'PATH_INFO':path,'REQUEST_METHOD':method,'QUERY_STRING':query},
                          lambda s,h:status.append((s,h))))
        return status[0][0],json.loads(body),dict(status[0][1])
    def test_authorized_venue_isolation(self):
        a=self.call(lambda _: {'venue_id':'A','permissions':{'tables:read'}})
        b=self.call(lambda _: {'venue_id':'B','permissions':{'tables:read'}})
        self.assertEqual(a[0],'200 OK')
        self.assertEqual(a[1]['tables'],[{'id':'T1','physical_seats':4,'occupied_guests':2}])
        self.assertEqual(a[1]['placements'][0]['x_percent'],25)
        self.assertEqual(a[1]['revision'],3)
        self.assertEqual(b[1]['tables'][0]['physical_seats'],6)
        self.assertEqual(b[1]['revision'],8)
        self.assertEqual(a[2]['Cache-Control'],'no-store')
    def test_unauthenticated_and_menu_only_denied(self):
        self.assertEqual(self.call(lambda _:None)[0],'401 Unauthorized')
        self.assertEqual(self.call(lambda _:{'venue_id':'A','permissions':{'menu:read'}})[0],'403 Forbidden')
        self.assertEqual(self.call(lambda _:{'venue_id':'','permissions':{'tables:read'}})[0],'403 Forbidden')
    def test_rejects_queries_and_writes(self):
        allowed=lambda _:{'venue_id':'A','permissions':{'tables:read'}}
        self.assertEqual(self.call(allowed,query='venue_id=B')[0],'400 Bad Request')
        self.assertEqual(self.call(allowed,method='PATCH')[0],'405 Method Not Allowed')
        self.assertEqual(self.call(allowed,path='/api/v1/menu-items')[0],'404 Not Found')
    def test_missing_catalog_returns_empty_not_demo_data(self):
        status,data,_=self.call(lambda _:{'venue_id':'C','permissions':{'tables:read'}})
        self.assertEqual(status,'200 OK')
        self.assertEqual(data,{'revision':0,'tables':[],'placements':[]})
    def test_sqlite_failures_are_sanitized(self):
        def fail(_):raise sqlite3.OperationalError('secret database path')
        status,data,_=self.call(fail)
        self.assertEqual(status,'503 Service Unavailable')
        self.assertEqual(data,{'error':'temporarily_unavailable'})
        self.db.execute('DROP TABLE floor_physical_tables')
        status,data,_=self.call(lambda _:{'venue_id':'A','permissions':{'tables:read'}})
        self.assertEqual(status,'503 Service Unavailable')
        self.assertNotIn('secret',str(data))

if __name__=='__main__':
    unittest.main()
