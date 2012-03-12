from __future__ import unicode_literals
from io import BytesIO, StringIO
import unittest

from saucebrush.sources import CSVSource, FixedWidthFileSource

class SourceTestCase(unittest.TestCase):

    def _get_csv(self):
        data = '''a,b,c
1,2,3
5,5,5
1,10,100'''
        return StringIO(data)

    def test_csv_source_basic(self):
        source = CSVSource(self._get_csv())
        expected_data = [{'a':'1', 'b':'2', 'c':'3'},
                         {'a':'5', 'b':'5', 'c':'5'},
                         {'a':'1', 'b':'10', 'c':'100'}]
        self.assertEqual(list(source), expected_data)

    def test_csv_source_fieldnames(self):
        source = CSVSource(self._get_csv(), ['x','y','z'])
        expected_data = [{'x':'a', 'y':'b', 'z':'c'},
                         {'x':'1', 'y':'2', 'z':'3'},
                         {'x':'5', 'y':'5', 'z':'5'},
                         {'x':'1', 'y':'10', 'z':'100'}]
        self.assertEqual(list(source), expected_data)

    def test_csv_source_skiprows(self):
        source = CSVSource(self._get_csv(), skiprows=1)
        expected_data = [{'a':'5', 'b':'5', 'c':'5'},
                         {'a':'1', 'b':'10', 'c':'100'}]
        self.assertEqual(list(source), expected_data)

    def test_fixed_width_source(self):
        data = StringIO('JamesNovember 3 1986\nTim  September151999')
        fields = (('name',5), ('month',9), ('day',2), ('year',4))
        source = FixedWidthFileSource(data, fields)
        expected_data = [{'name':'James', 'month':'November', 'day':'3',
                          'year':'1986'},
                         {'name':'Tim', 'month':'September', 'day':'15',
                          'year':'1999'}]
        self.assertEqual(list(source), expected_data)

if __name__ == '__main__':
    unittest.main()
