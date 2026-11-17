"""Offline stock movement reason/sign validation (not yet wired into SQLite ledger)."""
import unittest

ALLOWED = {'receipt': 1, 'use': -1, 'waste': -1, 'correction': 0}
MAX_DELTA = 10**12


def validate_stock_movement(delta, reason, *, correction_reference=None):
    """Validate signed base-unit movement and explicit correction provenance."""
    if type(delta) is not int or delta == 0 or abs(delta) > MAX_DELTA:
        raise ValueError('invalid integer stock delta')
    if reason not in ALLOWED:
        raise ValueError('unsupported stock movement reason')
    direction = ALLOWED[reason]
    if direction and delta * direction <= 0:
        raise ValueError('stock movement direction conflicts with reason')
    if reason == 'correction':
        if not isinstance(correction_reference, str) or not correction_reference.strip():
            raise ValueError('correction requires referenced event')
    elif correction_reference is not None:
        raise ValueError('reference only allowed for corrections')
    return True


class StockReasonPolicyTests(unittest.TestCase):
    def test_valid_movements(self):
        for delta, reason, reference in [(10, 'receipt', None), (-2, 'use', None),
                                         (-3, 'waste', None), (4, 'correction', 'e1'),
                                         (-4, 'correction', 'e1')]:
            self.assertTrue(validate_stock_movement(delta, reason, correction_reference=reference))

    def test_wrong_sign(self):
        for delta, reason in [(-1, 'receipt'), (1, 'use'), (1, 'waste')]:
            with self.assertRaises(ValueError):
                validate_stock_movement(delta, reason)

    def test_invalid_quantity(self):
        for delta in [0, True, 1.5, 10**12 + 1]:
            with self.assertRaises(ValueError):
                validate_stock_movement(delta, 'receipt')

    def test_correction_provenance(self):
        for reference in [None, '', '  ']:
            with self.assertRaises(ValueError):
                validate_stock_movement(1, 'correction', correction_reference=reference)
        with self.assertRaises(ValueError):
            validate_stock_movement(1, 'receipt', correction_reference='e1')

    def test_unknown_reason(self):
        with self.assertRaises(ValueError):
            validate_stock_movement(1, 'purchase')


if __name__ == '__main__':
    unittest.main()
