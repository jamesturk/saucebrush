import doctest
import unittest
from saucebrush import Recipe
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


class RecipeTestCase(unittest.TestCase):
    def test_error_stream(self):
        saver = Saver()
        recipe = Recipe(Raiser(), error_stream=saver)
        recipe.run([{'a': 1}, {'b': 2}])
        self.assertEqual(saver.saved, [{'a': 1}, {'b': 2}])


if __name__ == '__main__':
    unittest.main()
