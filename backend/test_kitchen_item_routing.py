import unittest
from kitchen_item_routing import OrderLine, route_order


class RoutingTests(unittest.TestCase):
    def route(self, lines, **kwargs):
        return route_order(authorized_venue_id=kwargs.get("actor", "v1"),
                           order_venue_id="v1", order_id="o1",
                           order_status=kwargs.get("status", "accepted"), lines=lines)

    def test_split_and_preserve_quantities(self):
        batches = self.route((OrderLine("a", "soup", 2, "kitchen"),
                              OrderLine("b", "tea", 3, "bar"),
                              OrderLine("c", "salad", 1, "kitchen")))
        self.assertEqual([b.station for b in batches], ["kitchen", "bar"])
        self.assertEqual([l.quantity for l in batches[0].lines], [2, 1])
        self.assertEqual(batches[1].lines[0].item_id, "tea")

    def test_cross_venue_rejected(self):
        with self.assertRaises(PermissionError):
            self.route((OrderLine("a", "x", 1, "bar"),), actor="v2")

    def test_unaccepted_rejected(self):
        with self.assertRaises(ValueError):
            self.route((OrderLine("a", "x", 1, "bar"),), status="draft")

    def test_duplicate_line_rejected(self):
        with self.assertRaises(ValueError):
            self.route((OrderLine("a", "x", 1, "bar"), OrderLine("a", "y", 1, "kitchen")))

    def test_bad_quantity_and_station_rejected(self):
        for quantity, station in ((0, "bar"), (True, "bar"), (1, "other")):
            with self.subTest(quantity=quantity, station=station), self.assertRaises(ValueError):
                self.route((OrderLine("a", "x", quantity, station),))

    def test_empty_order_rejected(self):
        with self.assertRaises(ValueError):
            self.route(())


if __name__ == "__main__":
    unittest.main()
