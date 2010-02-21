import unittest
from saucebrush.tests.filters import FilterTestCase
from saucebrush.tests.sources import SourceTestCase

filter_suite = unittest.TestLoader().loadTestsFromTestCase(FilterTestCase)
source_suite = unittest.TestLoader().loadTestsFromTestCase(SourceTestCase)

if __name__ == '__main__':
    unittest.main()
