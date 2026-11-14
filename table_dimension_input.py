"""Strict ASCII numeric form adapter for floor-plan dimensions (centimetres).

Parsing does not grant permission or save layout changes. Always use the
venue-scoped transactional update path after validating the submitted values.
"""
import re
from decimal import Decimal

from table_visual_dimensions import validate_visual_dimensions


_PATTERN = re.compile(r"[0-9]{1,3}(?:\.[0-9])?", re.ASCII)


def parse_dimension_cm(raw):
    """Parse an exact 0.5 cm-step numeric input without locale coercion."""
    if not isinstance(raw, str) or _PATTERN.fullmatch(raw) is None:
        raise ValueError("dimension must be ASCII digits with optional one decimal")
    value = Decimal(raw)
    # Delegate bounds and step enforcement to the established geometry contract.
    validate_visual_dimensions(value, value)
    return value


def parse_dimension_pair(width_raw, depth_raw):
    """Normalize a pair for the existing resize preflight contract."""
    return validate_visual_dimensions(parse_dimension_cm(width_raw),
                                      parse_dimension_cm(depth_raw))


if __name__ == "__main__":
    import unittest

    class DimensionInputTests(unittest.TestCase):
        def test_accepts_valid_form_values(self):
            self.assertEqual(parse_dimension_pair("030", "120.5"),
                             {"width_cm": "30.0", "depth_cm": "120.5"})
            self.assertEqual(parse_dimension_pair("500", "30.0"),
                             {"width_cm": "500.0", "depth_cm": "30.0"})

        def test_rejects_noncanonical_or_unsafe_inputs(self):
            for raw in ("", "0", "29.5", "500.5", "100.1", "80.25", " 80",
                        "80 ", "+80", "-80", "8e1", "80,5", "８０", "80\n",
                        "80\x00", "0000", "1_00", None, 80, 80.0, True, []):
                with self.subTest(raw=raw), self.assertRaises(ValueError):
                    parse_dimension_cm(raw)

        def test_rejects_invalid_second_dimension(self):
            with self.assertRaises(ValueError):
                parse_dimension_pair("100", "30.1")

    unittest.main()
