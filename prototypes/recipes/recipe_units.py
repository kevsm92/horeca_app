"""Exact offline recipe quantity normalization; no density assumptions."""
from fractions import Fraction

_FACTORS = {
    'mg': ('mass', 1), 'g': ('mass', 1000), 'kg': ('mass', 1000000),
    'ml': ('volume', 1), 'l': ('volume', 1000),
    'piece': ('count', 1),
}

def normalize_quantity(quantity, unit, target_unit):
    """Return exact integer target quantity; reject fractional target units."""
    if isinstance(quantity, bool) or not isinstance(quantity, (int, Fraction)) or quantity <= 0:
        raise ValueError('quantity must be a positive int or Fraction')
    if unit not in _FACTORS or target_unit not in _FACTORS:
        raise ValueError('unknown unit')
    dimension, factor = _FACTORS[unit]
    target_dimension, target_factor = _FACTORS[target_unit]
    if dimension != target_dimension:
        raise ValueError('incompatible dimensions; density conversions require approved data')
    result = Fraction(quantity * factor, target_factor)
    if result.denominator != 1:
        raise ValueError('quantity is not integral in target unit')
    return result.numerator
