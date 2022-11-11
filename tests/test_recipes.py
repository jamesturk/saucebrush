import pytest
from saucebrush import Recipe, run_recipe, SaucebrushError, OvercookedError
from saucebrush.filters import Filter


class Raiser(Filter):
    def process_record(self, record):
        raise Exception("bad record")


class Saver(Filter):
    def __init__(self):
        self.saved = []

    def process_record(self, record):
        self.saved.append(record)
        return record


def test_error_stream():
    saver = Saver()
    recipe = Recipe(Raiser(), error_stream=saver)
    recipe.run([{"a": 1}, {"b": 2}])
    recipe.done()

    assert saver.saved[0]["record"] == {"a": 1}
    assert saver.saved[1]["record"] == {"b": 2}

    # Must pass either a Recipe, a Filter or an iterable of Filters
    # as the error_stream argument
    assert pytest.raises(SaucebrushError, Recipe, error_stream=5)


def test_run_recipe():
    saver = Saver()
    run_recipe([1, 2], saver)

    assert saver.saved == [1, 2]


def test_done():
    saver = Saver()
    recipe = Recipe(saver)
    recipe.run([1])
    recipe.done()

    assert pytest.raises(OvercookedError, recipe.run, [2])
    assert pytest.raises(OvercookedError, recipe.done)
    assert saver.saved == [1]
