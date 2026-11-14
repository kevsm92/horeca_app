import unittest
from floor_keyboard_step import keyboard_move


class KeyboardMovementTests(unittest.TestCase):
    def move(self, key, **kwargs):
        return keyboard_move(100, 100, 200, 150, 1000, 800, key, **kwargs)

    def test_four_arrows(self):
        self.assertEqual(self.move('ArrowLeft'), (50, 100))
        self.assertEqual(self.move('ArrowRight'), (150, 100))
        self.assertEqual(self.move('ArrowUp'), (100, 50))
        self.assertEqual(self.move('ArrowDown'), (100, 150))

    def test_shift_accelerates_and_clamps(self):
        self.assertEqual(self.move('ArrowLeft', shift=True), (0, 100))
        self.assertEqual(self.move('ArrowUp', shift=True), (100, 0))
        self.assertEqual(keyboard_move(800, 650, 200, 150, 1000, 800,
                                      'ArrowRight'), (800, 650))

    def test_rejects_invalid_inputs(self):
        for overrides in ({'step_mm': True}, {'step_mm': 0}, {'shift': 1}):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                self.move('ArrowRight', **overrides)
        with self.assertRaises(ValueError):
            self.move('Enter')
        with self.assertRaises(ValueError):
            keyboard_move(900, 100, 200, 150, 1000, 800, 'ArrowLeft')
        with self.assertRaises(ValueError):
            keyboard_move(True, 100, 200, 150, 1000, 800, 'ArrowLeft')


if __name__ == '__main__':
    unittest.main()
