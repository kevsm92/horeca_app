"""Strict offline adapter for a table's numeric seat-count form field.

Never derive physical capacity from geometry. This adapter only parses input;
call the venue-scoped transactional resize guard before persisting.
"""
import re


def parse_seat_count(raw):
    """Accept ASCII decimal digits only, with no coercion or silent rounding."""
    if not isinstance(raw, str) or not re.fullmatch(r"[0-9]{1,3}", raw):
        raise ValueError("seat count must contain 1-3 ASCII digits")
    value = int(raw)
    if not 1 <= value <= 100:
        raise ValueError("seat count outside supported form bounds")
    return value


if __name__ == "__main__":
    import unittest

    class SeatInputTests(unittest.TestCase):
        def test_accepts_plain_ascii_integer(self):
            for raw, expected in (("1", 1), ("04", 4), ("100", 100)):
                self.assertEqual(parse_seat_count(raw), expected)

        def test_rejects_ambiguous_or_non_numeric(self):
            for raw in ("", "0", "101", "000", "0001", " 2", "2 ",
                        "+2", "-2", "2.0", "2e1", "2,0", "２", "²",
                        "2\n", "2\x00", None, 2, 2.0, True, [], {}):
                with self.subTest(raw=raw), self.assertRaises(ValueError):
                    parse_seat_count(raw)

    unittest.main()
