"""Offline comparable supplier quotes; no ordering or network I/O."""
from fractions import Fraction

_UNITS = {'g': ('mass', 1), 'kg': ('mass', 1000),
          'ml': ('volume', 1), 'l': ('volume', 1000),
          'each': ('count', 1)}


def comparable_quotes(db, venue_id, ingredient_id):
    """Active quotes cheapest per base unit first; reject mixed dimensions.

    Prices are exact Fraction EUR cents per g/ml/each.
    Caller must verify ingredient identity and packaging quality.
    """
    if not isinstance(venue_id, str) or not venue_id.strip():
        raise ValueError('venue_id is required')
    if not isinstance(ingredient_id, str) or not ingredient_id.strip():
        raise ValueError('ingredient_id is required')
    rows = db.execute('''SELECT k.supplier_id,s.display_name,k.sku,k.unit,
                                k.pack_quantity,k.price_cents,k.lead_days
                         FROM supplier_sku AS k
                         JOIN supplier AS s ON s.venue_id=k.venue_id
                              AND s.supplier_id=k.supplier_id
                         WHERE k.venue_id=? AND k.ingredient_id=? AND s.active=1''',
                      (venue_id, ingredient_id)).fetchall()
    dimensions = set()
    quotes = []
    for supplier_id, name, sku, unit, qty, cents, lead in rows:
        if unit not in _UNITS or type(qty) is not int or qty <= 0 or type(cents) is not int or cents < 0:
            raise ValueError('invalid stored supplier quote')
        dimension, factor = _UNITS[unit]
        dimensions.add(dimension)
        quotes.append((supplier_id, name, sku, Fraction(cents, qty * factor), lead))
    if len(dimensions) > 1:
        raise ValueError('mixed unit dimensions require human conversion review')
    return sorted(quotes, key=lambda q: (q[3], q[4], q[0], q[2]))
