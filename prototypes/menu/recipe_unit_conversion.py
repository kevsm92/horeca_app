"""Exact, dimension-safe recipe quantity normalization; offline only.

Base units: mg (mass), ml (volume), each (discrete). No density guesses.
"""
from fractions import Fraction

_FACTORS = {
    'mg': ('mass', 1), 'g': ('mass', 1000), 'kg': ('mass', 1000000),
    'ml': ('volume', 1), 'l': ('volume', 1000),
    'each': ('count', 1),
}
_BASE = {'mass': 'mg', 'volume': 'ml', 'count': 'each'}


def normalize_quantity(quantity, unit):
    """Return (exact Fraction in base units, base unit), never round silently."""
    if isinstance(quantity, bool) or not isinstance(quantity, (int, str, Fraction)):
        raise ValueError('quantity must be an integer, decimal string, or Fraction')
    try:
        amount = Fraction(quantity)
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError('invalid quantity') from exc
    if amount <= 0:
        raise ValueError('quantity must be positive')
    if unit not in _FACTORS:
        raise ValueError('unsupported unit')
    dimension, factor = _FACTORS[unit]
    result = amount * factor
    if dimension == 'count' and result.denominator != 1:
        raise ValueError('fractional discrete items not allowed')
    return result, _BASE[dimension]


def convert_quantity(quantity, source_unit, target_unit):
    """Convert within a dimension exactly; never infer mass-volume density."""
    amount, base = normalize_quantity(quantity, source_unit)
    if target_unit not in _FACTORS:
        raise ValueError('unsupported target unit')
    dimension, factor = _FACTORS[target_unit]
    if _BASE[dimension] != base:
        raise ValueError('incompatible dimensions; approved density required')
    return amount / factor
