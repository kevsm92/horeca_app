"""Offline recipe batch-to-portion cost allocation; estimates only, never menu prices."""


def portion_costs(batch_cost_cents, portions):
    """Allocate integer-cent batch cost deterministically without creating cents.

    Earlier portions receive remainder cents; zero-cost portions remain valid.
    The caller must supply an approved positive yield, not an inferred serving size.
    """
    if type(batch_cost_cents) is not int or batch_cost_cents < 0:
        raise ValueError('batch cost must be nonnegative integer cents')
    if type(portions) is not int or portions <= 0:
        raise ValueError('approved yield must be a positive integer')
    base, remainder = divmod(batch_cost_cents, portions)
    return [base + (1 if i < remainder else 0) for i in range(portions)]
