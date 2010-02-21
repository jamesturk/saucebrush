import unittest
from saucebrush.tests.filters import FilterTestCase

filter_suite = unittest.TestLoader().loadTestsFromTestCase(FilterTestCase)

if __name__ == '__main__':
    unittest.main()
