import json
import unittest
from bom_validation import validate_bom_snapshot


class BomValidationTests(unittest.TestCase):
    def test_valid_synthetic_components(self):
        data = [{'ingredient_id': 'fictional_flour', 'quantity': 125000, 'unit': 'mg'},
                {'ingredient_id': 'fictional_water', 'quantity': 200, 'unit': 'ml'}]
        self.assertEqual(validate_bom_snapshot(json.dumps(data)), data)

    def test_empty_or_invalid_json(self):
        for raw in ('[]', '{}', '{', 'null', None):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                validate_bom_snapshot(raw)

    def test_invalid_quantities(self):
        for value in (0, -1, True, 1.5, '2', 1_000_000_001):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_bom_snapshot(json.dumps([{'ingredient_id': 'x', 'quantity': value, 'unit': 'mg'}]))

    def test_unknown_units_and_fields(self):
        for component in ({'ingredient_id': 'x', 'quantity': 1, 'unit': 'kg'},
                          {'ingredient_id': 'x', 'quantity': 1, 'unit': 'mg', 'allergens': []}):
            with self.assertRaises(ValueError):
                validate_bom_snapshot(json.dumps([component]))

    def test_duplicate_or_invalid_identity(self):
        base = {'ingredient_id': 'x', 'quantity': 1, 'unit': 'count'}
        for data in ([base, base], [{**base, 'ingredient_id': ' x'}]):
            with self.assertRaises(ValueError):
                validate_bom_snapshot(json.dumps(data))


if __name__ == '__main__':
    unittest.main()
