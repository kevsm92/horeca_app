"""Offline recipe cost variance review gate; fictional quotes only.

A cost variance never changes menu prices or inventory and cannot self-approve.
The authorized venue is supplied by a trusted caller, never a request body.
"""
from recipe_cost_variance import compare_recipe_cost_quotes


def assess_cost_variance(previous, current, *, authorized_venue, review_threshold_cents):
    if not isinstance(authorized_venue, str) or not authorized_venue.strip():
        raise ValueError("trusted venue required")
    if type(review_threshold_cents) is not int or review_threshold_cents < 0:
        raise ValueError("nonnegative integer-cent threshold required")
    for snapshot in (previous, current):
        if not isinstance(snapshot, dict) or snapshot.get("venue_id") != authorized_venue:
            raise ValueError("venue mismatch or missing venue provenance")
        if not isinstance(snapshot.get("quote_revision"), int) or type(snapshot["quote_revision"]) is not int or snapshot["quote_revision"] <= 0:
            raise ValueError("positive quote revision required")
    if current["quote_revision"] <= previous["quote_revision"]:
        raise ValueError("new quote revision must be later")
    comparison = compare_recipe_cost_quotes(previous, current)
    delta = comparison["batch_cost_delta_cents"]
    return {**comparison,
            "previous_quote_revision": previous["quote_revision"],
            "current_quote_revision": current["quote_revision"],
            "review_threshold_cents": review_threshold_cents,
            "requires_manager_review": delta != 0 and abs(delta) >= review_threshold_cents,
            "approval_status": "not_approved",
            "effect": "review_only_no_price_or_stock_mutation"}
