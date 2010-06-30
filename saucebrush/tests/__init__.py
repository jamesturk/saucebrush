import unittest
from saucebrush.tests.filters import FilterTestCase
from saucebrush.tests.sources import SourceTestCase
from saucebrush.tests.emitters import EmitterTestCase
from saucebrush.tests.recipes import RecipeTestCase

filter_suite = unittest.TestLoader().loadTestsFromTestCase(FilterTestCase)
source_suite = unittest.TestLoader().loadTestsFromTestCase(SourceTestCase)
emitter_suite = unittest.TestLoader().loadTestsFromTestCase(EmitterTestCase)
recipe_suite = unittest.TestLoader().loadTestsFromTestCase(RecipeTestCase)

if __name__ == '__main__':
    unittest.main()
