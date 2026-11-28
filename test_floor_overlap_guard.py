import unittest
from floor_overlap_guard import validate_no_overlap


class FloorOverlapTests(unittest.TestCase):
    def test_disjoint_and_touching_edges(self):
        self.assertTrue(validate_no_overlap([('a', 0, 0, 100, 100), ('b', 100, 0, 50, 50)]))
        self.assertTrue(validate_no_overlap([]))

    def test_partial_and_contained_overlap(self):
        for second in [('b', 99, 99, 50, 50), ('b', 20, 20, 10, 10)]:
            with self.subTest(second=second), self.assertRaisesRegex(ValueError, 'overlapping'):
                validate_no_overlap([('a', 0, 0, 100, 100), second])

    def test_invalid_geometry_and_duplicates(self):
        for rows in [[('a', 0, 0, True, 20)], [('a', -1, 0, 20, 20)],
                     [('a', 0, 0, 0, 20)], [('a', 0, 0, 20, 20), ('a', 50, 0, 20, 20)],
                     [('a', 0, 0, 20)], [('a', 0.5, 0, 20, 20)]]:
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                validate_no_overlap(rows)

    def test_limit_and_immutable(self):
        rows = [('t' + str(i), i * 20, 0, 10, 10) for i in range(200)]
        original = list(rows)
        self.assertTrue(validate_no_overlap(rows))
        self.assertEqual(rows, original)
        with self.assertRaises(ValueError):
            validate_no_overlap(rows + [('extra', 5000, 0, 10, 10)])


if __name__ == '__main__':
    unittest.main()
