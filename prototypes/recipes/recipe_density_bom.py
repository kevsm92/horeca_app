"""Opt-in approved mass/volume conversion for offline recipe BOM entries.

Caller must supply an authenticated, server-derived venue. No inferred densities.
"""
from fractions import Fraction
from recipe_bom import add_component
from recipe_density_store import latest_approved_density
from recipe_units import normalize_quantity

MASS = {'mg', 'g', 'kg'}
VOLUME = {'ml', 'l'}


def add_approved_density_component(db, *, authorized_venue, recipe, ingredient,
                                   quantity, unit):
    """Add a component only when a current, venue-matched density permits exact units.

    Does not silently round ingredient quantities or use revoked approvals.
    """
    if not isinstance(authorized_venue, str) or not authorized_venue.strip():
        raise ValueError('trusted venue required')
    row = db.execute('SELECT unit FROM recipe_ingredients WHERE venue_id=? AND ingredient_id=?',
                     (authorized_venue, ingredient)).fetchone()
    if row is None:
        raise ValueError('unknown venue ingredient')
    target = row[0]
    if (unit in MASS and target in VOLUME) or (unit in VOLUME and target in MASS):
        approval = latest_approved_density(db, authorized_venue=authorized_venue,
                                           ingredient_id=ingredient)
        if approval is None:
            raise ValueError('current approved ingredient density required')
        ratio = Fraction(approval['mg_per_ml_numerator'], approval['mg_per_ml_denominator'])
        if unit in MASS:
            mg = normalize_quantity(quantity, unit, 'mg')
            converted = Fraction(mg, 1) / ratio
            target_quantity = converted / {'ml': 1, 'l': 1000}[target]
        else:
            ml = normalize_quantity(quantity, unit, 'ml')
            converted = ml * ratio
            target_quantity = converted / {'mg': 1, 'g': 1000, 'kg': 1000000}[target]
        if target_quantity.denominator != 1:
            raise ValueError('approved density yields fractional storage units')
        add_component(db, venue=authorized_venue, recipe=recipe, ingredient=ingredient,
                      quantity=target_quantity.numerator, unit=target)
    else:
        add_component(db, venue=authorized_venue, recipe=recipe, ingredient=ingredient,
                      quantity=quantity, unit=unit)
