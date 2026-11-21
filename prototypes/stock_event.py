"""Pure, synthetic-only order-to-inventory deduction planner.

No database writes, stock mutation, or external order submission.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Deduction:
    ingredient_id: str
    quantity_milliunits: int


def plan_deductions(order_id: str, lines: tuple[tuple[str, int], ...], recipes: dict[str, tuple[Deduction, ...]]) -> tuple[str, tuple[Deduction, ...]]:
    """Return deterministic event key and aggregated positive deductions.

    A durable ledger must enforce uniqueness of the returned key transactionally.
    """
    if not isinstance(order_id, str) or not order_id.strip():
        raise ValueError('order_id required')
    if not lines:
        raise ValueError('order lines required')
    totals: dict[str, int] = {}
    for menu_id, count in lines:
        if not isinstance(menu_id, str) or not menu_id or type(count) is not int or count <= 0:
            raise ValueError('invalid order line')
        if menu_id not in recipes or not recipes[menu_id]:
            raise ValueError('recipe missing')
        for component in recipes[menu_id]:
            if not component.ingredient_id or type(component.quantity_milliunits) is not int or component.quantity_milliunits <= 0:
                raise ValueError('invalid recipe component')
            totals[component.ingredient_id] = totals.get(component.ingredient_id, 0) + component.quantity_milliunits * count
    return f'order:{order_id}:stock-deduct:v1', tuple(Deduction(k, totals[k]) for k in sorted(totals))
