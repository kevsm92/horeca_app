"""Offline KDS-to-stock eligibility gate; synthetic order events only.

This pure gate does not record stock, authenticate a caller, or consume KDS messages.
An authorized adapter must verify the event against trusted persisted order state.
"""
import unittest

ELIGIBLE_TRANSITION = ('preparing', 'completed')


def eligible_consumption_event(*, prior_state, new_state, order_id, event_id):
    """Fail closed: only the first preparing->completed transition is eligible.

    The downstream ledger must still enforce venue-scoped idempotency and verify
    the authoritative KDS transition; client-provided states are not trusted.
    """
    for identifier in (order_id, event_id):
        if (not isinstance(identifier, str) or not 1 <= len(identifier) <= 128
                or not identifier.isascii()
                or not all(c.isalnum() or c in '-_' for c in identifier)):
            raise ValueError('invalid trusted event identity')
    if not isinstance(prior_state, str) or not isinstance(new_state, str):
        raise ValueError('invalid ticket state')
    return (prior_state, new_state) == ELIGIBLE_TRANSITION


class EligibilityTests(unittest.TestCase):
    def test_only_completion_from_preparing_is_eligible(self):
        self.assertTrue(eligible_consumption_event(prior_state='preparing', new_state='completed', order_id='o1', event_id='e1'))
        for before, after in [('queued', 'preparing'), ('queued', 'completed'),
                              ('completed', 'completed'), ('completed', 'voided'),
                              ('preparing', 'cancelled'), ('voided', 'completed')]:
            with self.subTest(before=before, after=after):
                self.assertFalse(eligible_consumption_event(prior_state=before, new_state=after, order_id='o1', event_id='e1'))

    def test_untrusted_identifiers_rejected(self):
        for bad in ('', ' ', 'a/b', 'a\n', 'é', 'x' * 129, None, True, 7):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    eligible_consumption_event(prior_state='preparing', new_state='completed', order_id=bad, event_id='e1')

    def test_invalid_state_type_fails_closed(self):
        for bad in (None, 7, ['preparing']):
            with self.assertRaises(ValueError):
                eligible_consumption_event(prior_state=bad, new_state='completed', order_id='o1', event_id='e1')


if __name__ == '__main__':
    unittest.main()
