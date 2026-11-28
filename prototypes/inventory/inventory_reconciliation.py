"""Read-only venue-scoped reconciliation of immutable stock events.

Offline synthetic reference. Caller must authorize venue before invoking.
"""
from collections import defaultdict


def reconcile_events(events, venue_id):
    """Return balances and reject conflicting retries or impossible event streams.

    Events must be in ledger insertion order, not arbitrary timestamp order.
    """
    if not isinstance(venue_id, str) or not venue_id:
        raise ValueError("invalid venue")
    seen = {}
    balances = defaultdict(int)
    for event in events:
        if not isinstance(event, dict):
            raise ValueError("invalid event")
        if event.get("venue_id") != venue_id:
            continue
        ingredient, event_id = event.get("ingredient_id"), event.get("event_id")
        delta, reason = event.get("delta"), event.get("reason")
        if not all(isinstance(x, str) and x for x in (ingredient, event_id, reason)):
            raise ValueError("invalid event identity")
        if type(delta) is not int or delta == 0 or abs(delta) > 10**12:
            raise ValueError("invalid delta")
        if reason not in {"receipt", "use", "waste", "correction"}:
            raise ValueError("invalid reason")
        if (reason == "receipt" and delta < 0) or (reason in {"use", "waste"} and delta > 0):
            raise ValueError("reason/sign mismatch")
        payload = (ingredient, delta, reason)
        if event_id in seen:
            if seen[event_id] != payload:
                raise ValueError("conflicting event ID")
            continue
        seen[event_id] = payload
        balances[ingredient] += delta
        if balances[ingredient] < 0:
            raise ValueError("negative stock at event " + event_id)
    return dict(sorted(balances.items()))
