"""Offline, exact-rational supplier unit-price comparison; never places orders."""
from fractions import Fraction
from supplier_directory import list_skus

_UNIT = {'g': ('mass', 1), 'kg': ('mass', 1000),
         'ml': ('volume', 1), 'l': ('volume', 1000),
         'each': ('count', 1)}


def compare_supplier_unit_prices(db, venue_id, ingredient_id):
    """Return cheapest-first comparable offers, grouped by physical dimension.

    unit_price_cents is an exact Fraction per g/ml/each, never a rounded
    float. Offers in different dimensions must never be ranked together.
    """
    if not isinstance(venue_id, str) or not venue_id.strip():
        raise ValueError('venue scope required')
    if not isinstance(ingredient_id, str) or not ingredient_id.strip():
        raise ValueError('ingredient scope required')
    groups = {'mass': [], 'volume': [], 'count': []}
    for supplier_id, name, sku, unit, quantity, cents, lead_days in list_skus(db, venue_id, ingredient_id):
        if unit not in _UNIT or type(quantity) is not int or quantity <= 0 or type(cents) is not int or cents < 0:
            raise ValueError('invalid persisted supplier offer')
        dimension, factor = _UNIT[unit]
        groups[dimension].append({
            'supplier_id': supplier_id, 'supplier_name': name, 'sku': sku,
            'unit': unit, 'pack_quantity': quantity, 'price_cents': cents,
            'lead_days': lead_days,
            'unit_price_cents': Fraction(cents, quantity * factor),
            'base_unit': {'mass': 'g', 'volume': 'ml', 'count': 'each'}[dimension],
        })
    return {dimension: sorted(offers, key=lambda o: (
        o['unit_price_cents'], o['lead_days'], o['supplier_id'], o['sku']))
        for dimension, offers in groups.items() if offers}
