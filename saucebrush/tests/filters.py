import unittest
import operator
import types
from saucebrush.filters import (Filter, YieldFilter, FieldFilter,
                                SubrecordFilter, ConditionalPathFilter,
                                ConditionalFilter, FieldModifier, FieldKeeper,
                                FieldRemover, FieldMerger, FieldAdder,
                                FieldCopier, FieldRenamer, Unique)

class DummyRecipe(object):
    rejected_record = None
    rejected_msg = None
    def reject_record(self, record, msg):
        self.rejected_record = record
        self.rejected_msg = msg

class Doubler(Filter):
    def process_record(self, record):
        return record*2

class OddRemover(Filter):
    def process_record(self, record):
        if record % 2 == 0:
            return record
        else:
            return None     # explicitly return None

class ListFlattener(YieldFilter):
    def process_record(self, record):
        for item in record:
            yield item

class FieldDoubler(FieldFilter):
    def process_field(self, item):
        return item*2

class NonModifyingFieldDoubler(Filter):
    def __init__(self, key):
        self.key = key

    def process_record(self, record):
        record = dict(record)
        record[self.key] *= 2
        return record

class ConditionalOddRemover(ConditionalFilter):
    def test_record(self, record):
        # return True for even values
        return record % 2 == 0

class FilterTestCase(unittest.TestCase):

    def _simple_data(self):
        return  [{'a':1, 'b':2, 'c':3},
                 {'a':5, 'b':5, 'c':5},
                 {'a':1, 'b':10, 'c':100}]

    def assert_filter_result(self, filter_obj, expected_data):
        result = filter_obj.attach(self._simple_data())
        self.assertEquals(list(result), expected_data)

    def test_reject_record(self):
        recipe = DummyRecipe()
        f = Doubler()
        result = f.attach([1,2,3], recipe=recipe)
        result.next()       # next has to be called for attach to take effect
        f.reject_record('bad', 'this one was bad')

        # ensure that the rejection propagated to the recipe
        self.assertEquals('bad', recipe.rejected_record)
        self.assertEquals('this one was bad', recipe.rejected_msg)

    def test_simple_filter(self):
        df = Doubler()
        result = df.attach([1,2,3])

        # ensure we got a generator that yields 2,4,6
        self.assertEquals(type(result), types.GeneratorType)
        self.assertEquals(list(result), [2,4,6])

    def test_simple_filter_return_none(self):
        cf = OddRemover()
        result = cf.attach(range(10))

        # ensure only even numbers remain
        self.assertEquals(list(result), [0,2,4,6,8])

    def test_simple_yield_filter(self):
        lf = ListFlattener()
        result = lf.attach([[1],[2,3],[4,5,6]])

        # ensure we got a generator that yields 1,2,3,4,5,6
        self.assertEquals(type(result), types.GeneratorType)
        self.assertEquals(list(result), [1,2,3,4,5,6])

    def test_simple_field_filter(self):
        ff = FieldDoubler(['a', 'c'])

        # check against expected data
        expected_data = [{'a':2, 'b':2, 'c':6},
                         {'a':10, 'b':5, 'c':10},
                         {'a':2, 'b':10, 'c':200}]
        self.assert_filter_result(ff, expected_data)

    def test_conditional_filter(self):
        cf = ConditionalOddRemover()
        result = cf.attach(range(10))

        # ensure only even numbers remain
        self.assertEquals(list(result), [0,2,4,6,8])

    ### Tests for Subrecord

    def test_subrecord_filter_list(self):
        data = [{'a': [{'b': 2}, {'b': 4}]},
                {'a': [{'b': 5}]},
                {'a': [{'b': 8}, {'b':2}, {'b':1}]}]

        expected = [{'a': [{'b': 4}, {'b': 8}]},
                {'a': [{'b': 10}]},
                {'a': [{'b': 16}, {'b':4}, {'b':2}]}]

        sf = SubrecordFilter('a', NonModifyingFieldDoubler('b'))
        result = sf.attach(data)

        self.assertEquals(list(result), expected)

    def test_subrecord_filter_deep(self):
        data = [{'a': {'d':[{'b': 2}, {'b': 4}]}},
                {'a': {'d':[{'b': 5}]}},
                {'a': {'d':[{'b': 8}, {'b':2}, {'b':1}]}}]

        expected = [{'a': {'d':[{'b': 4}, {'b': 8}]}},
                    {'a': {'d':[{'b': 10}]}},
                    {'a': {'d':[{'b': 16}, {'b':4}, {'b':2}]}}]

        sf = SubrecordFilter('a.d', NonModifyingFieldDoubler('b'))
        result = sf.attach(data)

        self.assertEquals(list(result), expected)

    def test_subrecord_filter_nonlist(self):
        data = [
            {'a':{'b':{'c':1}}},
            {'a':{'b':{'c':2}}},
            {'a':{'b':{'c':3}}},
        ]

        expected = [
            {'a':{'b':{'c':2}}},
            {'a':{'b':{'c':4}}},
            {'a':{'b':{'c':6}}},
        ]

        sf = SubrecordFilter('a.b', NonModifyingFieldDoubler('c'))
        result = sf.attach(data)

        self.assertEquals(list(result), expected)

    def test_subrecord_filter_list_in_path(self):
        data = [
            {'a': [{'b': {'c': 5}}, {'b': {'c': 6}}]},
            {'a': [{'b': {'c': 1}}, {'b': {'c': 2}}, {'b': {'c': 3}}]},
            {'a': [{'b': {'c': 2}} ]}
        ]

        expected = [
            {'a': [{'b': {'c': 10}}, {'b': {'c': 12}}]},
            {'a': [{'b': {'c': 2}}, {'b': {'c': 4}}, {'b': {'c': 6}}]},
            {'a': [{'b': {'c': 4}} ]}
        ]

        sf = SubrecordFilter('a.b', NonModifyingFieldDoubler('c'))
        result = sf.attach(data)

        self.assertEquals(list(result), expected)

    def test_conditional_path(self):

        predicate = lambda r: r['a'] == 1

        # double b if a == 1, otherwise double c
        cpf = ConditionalPathFilter(predicate, FieldDoubler('b'),
                                    FieldDoubler('c'))
        expected_data = [{'a':1, 'b':4, 'c':3},
                         {'a':5, 'b':5, 'c':10},
                         {'a':1, 'b':20, 'c':100}]

        self.assert_filter_result(cpf, expected_data)

    ### Tests for Generic Filters

    def test_field_modifier(self):
        # another version of FieldDoubler
        fm = FieldModifier(['a', 'c'], lambda x: x*2)

        # check against expected data
        expected_data = [{'a':2, 'b':2, 'c':6},
                         {'a':10, 'b':5, 'c':10},
                         {'a':2, 'b':10, 'c':200}]
        self.assert_filter_result(fm, expected_data)

    def test_field_keeper(self):
        fk = FieldKeeper(['c'])
        
        # check against expected results
        expected_data = [{'c':3}, {'c':5}, {'c':100}]
        self.assert_filter_result(fk, expected_data)

    def test_field_remover(self):
        fr = FieldRemover(['a', 'b'])

        # check against expected results
        expected_data = [{'c':3}, {'c':5}, {'c':100}]
        self.assert_filter_result(fr, expected_data)

    def test_field_merger(self):
        fm = FieldMerger({'sum':('a','b','c')}, lambda x,y,z: x+y+z)

        # check against expected results
        expected_data = [{'sum':6}, {'sum':15}, {'sum':111}]
        self.assert_filter_result(fm, expected_data)

    def test_field_merger_keep_fields(self):
        fm = FieldMerger({'sum':('a','b','c')}, lambda x,y,z: x+y+z,
                         keep_fields=True)

        # check against expected results
        expected_data = [{'a':1, 'b':2, 'c':3, 'sum':6},
                 {'a':5, 'b':5, 'c':5, 'sum':15},
                 {'a':1, 'b':10, 'c':100, 'sum': 111}]
        self.assert_filter_result(fm, expected_data)

    def test_field_adder_scalar(self):
        fa = FieldAdder('x', 7)

        expected_data = [{'a':1, 'b':2, 'c':3, 'x':7},
                 {'a':5, 'b':5, 'c':5, 'x':7},
                 {'a':1, 'b':10, 'c':100, 'x': 7}]
        self.assert_filter_result(fa, expected_data)

    def test_field_adder_callable(self):
        fa = FieldAdder('x', lambda: 7)

        expected_data = [{'a':1, 'b':2, 'c':3, 'x':7},
                 {'a':5, 'b':5, 'c':5, 'x':7},
                 {'a':1, 'b':10, 'c':100, 'x': 7}]
        self.assert_filter_result(fa, expected_data)

    def test_field_adder_iterable(self):
        fa = FieldAdder('x', [1,2,3])

        expected_data = [{'a':1, 'b':2, 'c':3, 'x':1},
                 {'a':5, 'b':5, 'c':5, 'x':2},
                 {'a':1, 'b':10, 'c':100, 'x': 3}]
        self.assert_filter_result(fa, expected_data)

    def test_field_adder_replace(self):
        fa = FieldAdder('b', lambda: 7)

        expected_data = [{'a':1, 'b':7, 'c':3},
                 {'a':5, 'b':7, 'c':5},
                 {'a':1, 'b':7, 'c':100}]
        self.assert_filter_result(fa, expected_data)

    def test_field_adder_no_replace(self):
        fa = FieldAdder('b', lambda: 7, replace=False)

        expected_data = [{'a':1, 'b':2, 'c':3},
                 {'a':5, 'b':5, 'c':5},
                 {'a':1, 'b':10, 'c':100}]
        self.assert_filter_result(fa, expected_data)

    def test_field_copier(self):
        fc = FieldCopier({'a2':'a', 'b2':'b'})

        expected_data = [{'a':1, 'b':2, 'c':3, 'a2':1, 'b2':2},
                         {'a':5, 'b':5, 'c':5, 'a2':5, 'b2':5},
                         {'a':1, 'b':10, 'c':100, 'a2': 1, 'b2': 10}]
        self.assert_filter_result(fc, expected_data)

    def test_field_renamer(self):
        fr = FieldRenamer({'x':'a', 'y':'b'})

        expected_data = [{'x':1, 'y':2, 'c':3},
                         {'x':5, 'y':5, 'c':5},
                         {'x':1, 'y':10, 'c':100}]
        self.assert_filter_result(fr, expected_data)

    # TODO: splitter & flattner tests?

    def test_unique_filter(self):
        u = Unique()
        in_data = [{'a': 77}, {'a':33}, {'a': 77}]
        expected_data = [{'a': 77}, {'a':33}]
        result = u.attach(in_data)

        self.assertEquals(list(result), expected_data)

    # TODO: unicode & string filter tests

if __name__ == '__main__':
    unittest.main()
