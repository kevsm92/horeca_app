"""Offline comparison of two approved-yield recipe cost snapshots.

Snapshots are estimates, not purchase prices, live inventory valuation or menu prices.
The caller must retrieve both snapshots under the same authenticated venue context.
"""


def compare_recipe_cost_quotes(previous, current):
    """Compare immutable integer-cent quote snapshots without floating point.

    Yield changes are refused: they would make per-portion comparisons misleading.
    Missing quotes, mismatched recipes and invalid totals fail closed.
    """
    def validate(quote):
        if not isinstance(quote, dict):
            raise ValueError('quote required')
        recipe = quote.get('recipe_id')
        yield_count = quote.get('approved_yield')
        batch = quote.get('estimated_batch_cost_cents')
        if not isinstance(recipe, str) or not recipe.strip():
            raise ValueError('recipe id required')
        if type(yield_count) is not int or yield_count <= 0:
            raise ValueError('positive approved yield required')
        if type(batch) is not int or batch < 0:
            raise ValueError('nonnegative integer-cent batch cost required')
        portions = quote.get('estimated_portion_costs_cents')
        if (not isinstance(portions, list) or len(portions) != yield_count
                or any(type(v) is not int or v < 0 for v in portions)
                or sum(portions) != batch):
            raise ValueError('portion allocation must conserve batch cents')
        return recipe, yield_count, batch

    old_recipe, old_yield, old_cost = validate(previous)
    new_recipe, new_yield, new_cost = validate(current)
    if old_recipe != new_recipe or old_yield != new_yield:
        raise ValueError('same recipe and approved yield required')
    delta = new_cost - old_cost
    return {
        'recipe_id': old_recipe,
        'approved_yield': old_yield,
        'previous_batch_cost_cents': old_cost,
        'current_batch_cost_cents': new_cost,
        'batch_cost_delta_cents': delta,
        'comparison_status': 'estimate_only_not_menu_price',
    }
