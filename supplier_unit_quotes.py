"""Offline, exact-unit supplier quote comparison; never orders stock."""
from fractions import Fraction
from supplier_directory import list_skus

_UNIT = {'g': ('mass', 1), 'kg': ('mass', 1000),
         'ml': ('volume', 1), 'l': ('volume', 1000),
         'each': ('count', 1)}


def compare_unit_quotes(db, venue_id, ingredient_id, target_unit):
    """Return (supplier, sku, cents-per-target-unit Fraction, lead_days).

    Exact rational prices prevent rounding-induced ranking errors. Quotes for
    incompatible dimensions are omitted, not silently compared.
    """
    if not isinstance(venue_id, str) or not venue_id.strip():
        raise ValueError('venue_id required')
    if not isinstance(ingredient_id, str) or not ingredient_id.strip():
        raise ValueError('ingredient_id required')
    if target_unit not in _UNIT:
        raise ValueError('unsupported target unit')
    dimension, target_scale = _UNIT[target_unit]
    quotes = []
    for supplier, _name, sku, unit, quantity, cents, lead_days in list_skus(db, venue_id, ingredient_id):
        if unit not in _UNIT or _UNIT[unit][0] != dimension:
            continue
        if type(quantity) is not int or quantity <= 0 or type(cents) is not int or cents < 0:
            raise ValueError('invalid stored supplier quote')
        rate = Fraction(cents * target_scale, quantity * _UNIT[unit][1])
        quotes.append((supplier, sku, rate, lead_days))
    return sorted(quotes, key=lambda q: (q[2], q[3], q[0], q[1]))
