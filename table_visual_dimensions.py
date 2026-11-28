"""Offline validation of floor-plan visual dimensions, independent of seat capacity.

The caller must authorize the venue and verify physical table ownership.
This function does not update inventory, seating or saved layout state.
"""
from decimal import Decimal, InvalidOperation

MIN_CM = Decimal("30")
MAX_CM = Decimal("500")
STEP_CM = Decimal("0.5")


def validate_visual_dimensions(width_cm, depth_cm):
    """Normalize centimetre dimensions; reject ambiguous or unsafe values."""
    result = {}
    for label, value in (("width_cm", width_cm), ("depth_cm", depth_cm)):
        if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
            raise ValueError(f"{label} must be numeric")
        try:
            number = Decimal(str(value))
        except InvalidOperation as exc:
            raise ValueError(f"{label} must be finite") from exc
        if not number.is_finite() or not MIN_CM <= number <= MAX_CM:
            raise ValueError(f"{label} must be between 30 and 500 cm")
        if number % STEP_CM:
            raise ValueError(f"{label} must use 0.5 cm increments")
        result[label] = f"{number:.1f}"
    return result


if __name__ == "__main__":
    import unittest

    class DimensionTests(unittest.TestCase):
        def test_bounds_and_normalization(self):
            self.assertEqual(validate_visual_dimensions(30, 500),
                             {"width_cm": "30.0", "depth_cm": "500.0"})
            self.assertEqual(validate_visual_dimensions(120.5, Decimal("80")),
                             {"width_cm": "120.5", "depth_cm": "80.0"})

        def test_reject_invalid_values(self):
            for invalid in (True, None, "120", 29.5, 500.5, 80.25,
                            float("nan"), float("inf"), -1, 0):
                with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                    validate_visual_dimensions(invalid, 80)
                with self.subTest(depth=invalid), self.assertRaises(ValueError):
                    validate_visual_dimensions(80, invalid)

        def test_no_seat_count_in_result(self):
            self.assertEqual(set(validate_visual_dimensions(100, 100)),
                             {"width_cm", "depth_cm"})

    unittest.main()
