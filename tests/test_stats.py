from saucebrush.stats import Sum, Average, Median, MinMax, StandardDeviation, Histogram


def _simple_data():
    return [
        {"a": 1, "b": 2, "c": 3},
        {"a": 5, "b": 5, "c": 5},
        {"a": 1, "b": 10, "c": 100},
    ]


def test_sum():
    fltr = Sum("b")
    list(fltr.attach(_simple_data()))
    assert fltr.value() == 17


def test_average():
    fltr = Average("c")
    list(fltr.attach(_simple_data()))
    assert fltr.value() == 36.0


def test_median():
    # odd number of values
    fltr = Median("a")
    list(fltr.attach(_simple_data()))
    assert fltr.value() == 1

    # even number of values
    fltr = Median("a")
    list(fltr.attach(_simple_data()[:2]))
    assert fltr.value() == 3


def test_minmax():
    fltr = MinMax("b")
    list(fltr.attach(_simple_data()))
    assert fltr.value() == (2, 10)


def test_standard_deviation():
    fltr = StandardDeviation("c")
    list(fltr.attach(_simple_data()))
    assert fltr.average() == 36.0
    assert fltr.median() == 5
    assert fltr.value() == (55.4346462061408, 3073.0)
    assert fltr.value(True) == (45.2621990922521, 2048.6666666666665)


def test_histogram():
    fltr = Histogram("a")
    fltr.label_length = 1
    list(fltr.attach(_simple_data()))
    assert str(fltr) == "\n1 **\n5 *\n"
