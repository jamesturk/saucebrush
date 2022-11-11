import unittest
from saucebrush.stats import Sum, Average, Median, MinMax, StandardDeviation, Histogram


class StatsTestCase(unittest.TestCase):
    def _simple_data(self):
        return [
            {"a": 1, "b": 2, "c": 3},
            {"a": 5, "b": 5, "c": 5},
            {"a": 1, "b": 10, "c": 100},
        ]

    def test_sum(self):
        fltr = Sum("b")
        list(fltr.attach(self._simple_data()))
        self.assertEqual(fltr.value(), 17)

    def test_average(self):
        fltr = Average("c")
        list(fltr.attach(self._simple_data()))
        self.assertEqual(fltr.value(), 36.0)

    def test_median(self):
        # odd number of values
        fltr = Median("a")
        list(fltr.attach(self._simple_data()))
        self.assertEqual(fltr.value(), 1)

        # even number of values
        fltr = Median("a")
        list(fltr.attach(self._simple_data()[:2]))
        self.assertEqual(fltr.value(), 3)

    def test_minmax(self):
        fltr = MinMax("b")
        list(fltr.attach(self._simple_data()))
        self.assertEqual(fltr.value(), (2, 10))

    def test_standard_deviation(self):
        fltr = StandardDeviation("c")
        list(fltr.attach(self._simple_data()))
        self.assertEqual(fltr.average(), 36.0)
        self.assertEqual(fltr.median(), 5)
        self.assertEqual(fltr.value(), (55.4346462061408, 3073.0))
        self.assertEqual(fltr.value(True), (45.2621990922521, 2048.6666666666665))

    def test_histogram(self):
        fltr = Histogram("a")
        fltr.label_length = 1
        list(fltr.attach(self._simple_data()))
        self.assertEqual(str(fltr), "\n1 **\n5 *\n")


if __name__ == "__main__":
    unittest.main()
