"""Pure, offline retry policy for HORECA transactional outbox dispatch.

This module never sends events. All timestamps are UTC-aware and supplied by caller.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta

MAX_ATTEMPTS = 5
BASE_DELAY_SECONDS = 30
MAX_DELAY_SECONDS = 900


@dataclass(frozen=True)
class RetryDecision:
    status: str
    attempts: int
    next_attempt_at: datetime | None


def decide_retry(attempts: int, now: datetime, *, permanent: bool = False) -> RetryDecision:
    """Return a deterministic retry/dead-letter decision after a failed delivery.

    attempts includes the just-failed attempt. The caller must atomically persist
    the result with its event and lease/fencing ownership; this function does not
    implement delivery, locking, deduplication, or transactional persistence.
    """
    if isinstance(attempts, bool) or not isinstance(attempts, int) or attempts < 1:
        raise ValueError("attempts must be a positive integer")
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    if now.utcoffset() != timedelta(0):
        raise ValueError("now must be UTC")
    if not isinstance(permanent, bool):
        raise ValueError("permanent must be boolean")
    if permanent or attempts >= MAX_ATTEMPTS:
        return RetryDecision("dead_letter", attempts, None)
    delay = min(BASE_DELAY_SECONDS * (2 ** (attempts - 1)), MAX_DELAY_SECONDS)
    return RetryDecision("retry_pending", attempts, now + timedelta(seconds=delay))
