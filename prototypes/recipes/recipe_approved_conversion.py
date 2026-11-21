"""Offline venue-scoped, explicitly approved ingredient density conversion.

Density is supplied as an exact mass-in-mg per volume-in-ml ratio.
No generic food density or cross-ingredient conversion is assumed.
"""
from fractions import Fraction
from recipe_units import normalize_quantity


def convert_with_approved_density(quantity, source_unit, target_unit, *,
                                  authorized_venue, ingredient_id, approval):
    """Convert mass/volume only with a matching approved, versioned record.

    approval is trusted server-side data, not a request payload. Reject revoked
    or mismatched records and non-integral target units. Never round stock units.
    """
    if not isinstance(authorized_venue, str) or not authorized_venue.strip():
        raise ValueError('trusted venue required')
    if not isinstance(ingredient_id, str) or not ingredient_id.strip():
        raise ValueError('ingredient required')
    if not isinstance(approval, dict):
        raise ValueError('approved density record required')
    if approval.get('venue_id') != authorized_venue or approval.get('ingredient_id') != ingredient_id:
        raise ValueError('density approval scope mismatch')
    if approval.get('status') != 'approved':
        raise ValueError('density approval not active')
    if type(approval.get('revision')) is not int or approval['revision'] < 1:
        raise ValueError('positive approval revision required')
    numerator = approval.get('mg_per_ml_numerator')
    denominator = approval.get('mg_per_ml_denominator')
    if type(numerator) is not int or type(denominator) is not int or numerator <= 0 or denominator <= 0:
        raise ValueError('positive exact density ratio required')
    mass_units = ('mg', 'g', 'kg')
    volume_units = ('ml', 'l')
    if source_unit in mass_units and target_unit in volume_units:
        mass_mg = normalize_quantity(quantity, source_unit, 'mg')
        volume_ml = Fraction(mass_mg * denominator, numerator)
        return normalize_quantity(volume_ml, 'ml', target_unit)
    if source_unit in volume_units and target_unit in mass_units:
        volume_ml = normalize_quantity(quantity, source_unit, 'ml')
        mass_mg = Fraction(volume_ml * numerator, denominator)
        return normalize_quantity(mass_mg, 'mg', target_unit)
    raise ValueError('density conversion requires mass-to-volume or volume-to-mass')
