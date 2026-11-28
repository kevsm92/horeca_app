"""Offline advisory shortlist: only fresh supplier quotes, exact units, no purchasing.

Displayed prices are current directory values, not historical revision quotes.
This shortlist is not authorization to place orders or proof of quoted prices.
"""
from functools import cmp_to_key

from supplier_directory import list_skus
from supplier_quote_freshness_view import supplier_quote_freshness


def fresh_quote_shortlist(db, venue_id, ingredient_id, unit, as_of, max_age_days):
    """Return (supplier_id, sku, directory_price_cents, pack_quantity, lead_days).

    Requires a latest quote revision classified current. Historical quote
    prices are intentionally not substituted for directory prices.
    """
    if unit not in ('g', 'kg', 'ml', 'l', 'each'):
        raise ValueError('recognized exact unit required')
    current = {(supplier, sku) for supplier, sku, _price, status, _stamp in
               supplier_quote_freshness(db, venue_id, ingredient_id, as_of, max_age_days)
               if status == 'current'}
    rows = [(supplier, sku, cents, quantity, lead) for
            supplier, _name, sku, row_unit, quantity, cents, lead in
            list_skus(db, venue_id, ingredient_id)
            if row_unit == unit and (supplier, sku) in current]

    def compare(a, b):
        # Exact rational comparison; no floating point currency arithmetic.
        left, right = a[2] * b[3], b[2] * a[3]
        return ((left > right) - (left < right)
                or (a[4] > b[4]) - (a[4] < b[4])
                or ((a[0], a[1]) > (b[0], b[1])) - ((a[0], a[1]) < (b[0], b[1])))

    return sorted(rows, key=cmp_to_key(compare))
