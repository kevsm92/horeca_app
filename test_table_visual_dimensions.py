"""Discoverable regression coverage for offline table visual-dimension validation.

Run: python -m unittest -v test_table_visual_dimensions
No database, network, real venue data or payment integration is used.
"""
import unittest
from decimal import Decimal

from table_visual_dimensions import validate_visual_dimensions


class VisualDimensionContractTests(unittest.TestCase):
    def test_both_boundaries_and_half_centimetre_steps(self):
        self.assertEqual(validate_visual_dimensions(30, 500),
                         {"width_cm": "30.0", "depth_cm": "500.0"})
        self.assertEqual(validate_visual_dimensions(Decimal("30.5"), 499.5),
                         {"width_cm": "30.5", "depth_cm": "499.5"})

    def test_reject_non_numeric_and_non_finite_on_either_axis(self):
        invalid = [None, True, False, "120", b"120", [], {},
                   float("nan"), float("inf"), -float("inf"),
                   Decimal("NaN"), Decimal("Infinity")]
        for value in invalid:
            for axis in (0, 1):
                args = [100, 80]
                args[axis] = value
                with self.subTest(value=repr(value), axis=axis):
                    with self.assertRaises(ValueError):
                        validate_visual_dimensions(*args)

    def test_reject_out_of_range_and_sub_half_centimetre_values(self):
        for value in (0, -1, 29.5, 500.5, 501, 30.25, 499.75,
                      Decimal("100.01")):
            for axis in (0, 1):
                args = [100, 80]
                args[axis] = value
                with self.subTest(value=str(value), axis=axis):
                    with self.assertRaises(ValueError):
                        validate_visual_dimensions(*args)

    def test_visual_result_never_contains_seats_or_mutates_inputs(self):
        dimensions = [Decimal("120.5"), Decimal("80.0")]
        original = dimensions.copy()
        result = validate_visual_dimensions(*dimensions)
        self.assertEqual(dimensions, original)
        self.assertEqual(result, {"width_cm": "120.5", "depth_cm": "80.0"})
        self.assertEqual(set(result), {"width_cm", "depth_cm"})


if __name__ == "__main__":
    unittest.main()
