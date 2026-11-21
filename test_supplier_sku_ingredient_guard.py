import sqlite3
import unittest

from supplier_directory import initialize, add_supplier, add_sku
from supplier_sku_lookup import resolve_supplier_sku


class SupplierSkuIngredientGuardTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        initialize(self.db)
        for venue, ingredient in (("a", "flour"), ("b", "milk")):
            add_supplier(self.db, venue, "shared", "Fictional Vendor")
            add_sku(self.db, venue, "shared", "S-1", ingredient, "kg", 10, 1200, 3)

    def tearDown(self):
        self.db.close()

    def test_expected_ingredient_matches_only_same_venue(self):
        self.assertEqual(
            resolve_supplier_sku(self.db, venue_id="a", supplier_id="shared",
                                 sku="S-1", expected_ingredient_id="flour")["ingredient_id"],
            "flour",
        )
        self.assertIsNone(resolve_supplier_sku(
            self.db, venue_id="a", supplier_id="shared",
            sku="S-1", expected_ingredient_id="milk",
        ))
        self.assertIsNone(resolve_supplier_sku(
            self.db, venue_id="b", supplier_id="shared",
            sku="S-1", expected_ingredient_id="flour",
        ))

    def test_legacy_lookup_unchanged(self):
        self.assertEqual(resolve_supplier_sku(
            self.db, venue_id="b", supplier_id="shared", sku="S-1",
        )["ingredient_id"], "milk")

    def test_invalid_expected_ingredient_rejected(self):
        for value in ("", "  ", 12):
            with self.subTest(value=value), self.assertRaises(ValueError):
                resolve_supplier_sku(
                    self.db, venue_id="a", supplier_id="shared",
                    sku="S-1", expected_ingredient_id=value,
                )


if __name__ == "__main__":
    unittest.main()
