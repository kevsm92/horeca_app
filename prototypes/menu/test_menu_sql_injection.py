"""Regression: menu catalog scope and filter values must remain SQL parameters."""
import tempfile
import unittest
from pathlib import Path
from menu_catalog import connect, list_items, seed_synthetic


class MenuSqlInjectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = connect(Path(self.tmp.name) / 'catalog.sqlite')
        seed_synthetic(self.db, venue_id='venue-a')
        seed_synthetic(self.db, venue_id='venue-b')

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_sql_metacharacters_in_authorized_venue_do_not_escape_scope(self):
        for injected in ("venue-a' OR 1=1 --", "venue-a' UNION SELECT * FROM menu_items --", "venue-a; DROP TABLE menu_items; --"):
            with self.subTest(injected=injected):
                self.assertEqual(list_items(self.db, authorized_venue_id=injected), [])
        self.assertEqual(len(list_items(self.db, authorized_venue_id='venue-a')), 2)

    def test_sql_metacharacters_in_kind_are_rejected(self):
        with self.assertRaises(ValueError):
            list_items(self.db, authorized_venue_id='venue-a', kind="food' OR 1=1 --")

    def test_venue_filter_remains_effective_with_identical_item_ids(self):
        self.db.execute("UPDATE menu_items SET price_cents=999 WHERE venue_id='venue-b' AND item_id='demo-food-1'")
        a = list_items(self.db, authorized_venue_id='venue-a', kind='food')
        b = list_items(self.db, authorized_venue_id='venue-b', kind='food')
        self.assertEqual([item['price_cents'] for item in a], [650])
        self.assertEqual([item['price_cents'] for item in b], [999])


if __name__ == '__main__':
    unittest.main()
