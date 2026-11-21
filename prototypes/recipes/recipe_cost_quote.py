"""Offline estimated recipe portion quote from a trusted venue-scoped BOM.

Not a sale price, live stock valuation, or allergen certification.
"""
from recipe_bom import recipe_summary
from recipe_portions import portion_costs


def quote_recipe_portions(db, *, authorized_venue, recipe, approved_yield):
    """Return an integer-cent cost estimate or None for an unknown recipe.

    The venue must be derived from an authenticated server-side context by caller.
    """
    if type(approved_yield) is not int or approved_yield <= 0:
        raise ValueError('approved yield must be a positive integer')
    summary = recipe_summary(db, authorized_venue=authorized_venue, recipe=recipe)
    if summary is None:
        return None
    allocations = portion_costs(summary['estimated_cost_cents'], approved_yield)
    return {
        'recipe_id': summary['recipe_id'],
        'estimated_batch_cost_cents': summary['estimated_cost_cents'],
        'approved_yield': approved_yield,
        'estimated_portion_costs_cents': allocations,
        'allergens': summary['allergens'],
        'allergen_status': summary['allergen_status'],
        'pricing_status': 'estimate_not_menu_price',
    }
