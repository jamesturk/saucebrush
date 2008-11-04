"""
    Saucebrush Filters are callables that take a Saucebrush source and yield
    back filtered records.

    The Filter, YieldFilter, and FieldFilter abstract base types are provided
    for convenience.  Derived classes only need to implement process_record
    (or process_field for FieldFilter).
"""

from exceptions import NotImplementedError
from saucebrush import utils

######################
## Abstract Filters ##
######################

class Filter(object):
    """ ABC for filters that operate on records.

        All derived filters must provide a process_record(self, record) that
        takes a single record (python dictionary) and returns a result.
    """

    def __init__(self):
        pass

    def process_record(self, record):
        """ Abstract method to be overridden.

            Called with a single record, should return modified record.
        """
        raise NotImplementedError('process_record not defined in ' +
                                  self.__class__.__name__)

    def __call__(self, source):
        for record in source:
            yield self.process_record(record)


class YieldFilter(Filter):
    """ ABC for defining filters where process_record yields.

        If process_record cannot return exactly one result for every record
        it is passed, it should yield back as many records as needed and the
        filter must derive from YieldFilter.
    """
    def __init__(self):
        super(YieldFilter, self).__init__()

    def __call__(self, source):
        for record in source:
            for result in self.process_record(record):
                yield result


class FieldFilter(Filter):
    """ ABC for filters that do a single operation on individual fields.

        All derived filters must provide a process_field(self, item) that
        returns a modified item.  process_field is called on one or more keys
        passed into __init__.
    """

    def __init__(self, keys):
        super(FieldFilter, self).__init__()
        self._target_keys = keys

    def process_record(self, record):
        """ Calls process_field on all keys passed to __init__. """
        for key in self._target_keys:
            record[key] = self.process_field(record[key])
        return record

    def process_field(self, item):
        """ Given a value, return the value that it should be replaced with. """
        raise NotImplementedError('process_field not defined in ' +
                                  self.__class__.__name__)

    def __unicode__(self):
        return '%s( %s )' % (self.__class__.__name__, str(self._target_keys))


#####################
## Generic Filters ##
#####################

class FieldModifier(FieldFilter):
    """ Filter that calls a given function on a given set of fields.

        FieldModifier(('spam','eggs'), abs) to call the abs method on the spam
        and eggs fields in each record filtered.
    """

    def __init__(self, keys, func):
        super(FieldModifier, self).__init__(keys)
        self._filter_func = func

    def process_field(self, item):
        return self._filter_func(item)

    def __unicode__(self):
        return '%s( %s, %s )' % (self.__class__.__name__, str(self._target_keys),
                                 str(self._filter_func))


class FieldRemover(Filter):
    """ Filter that removes a given set of fields.

        FieldRemover(('spam', 'eggs')) removes the spam and eggs fields from
        every record filtered.
    """

    def __init__(self, keys):
        super(FieldRemover, self).__init__()
        self._target_keys = keys

    def process_record(self, record):
        for key in self._target_keys:
            record.pop(key, None)
        return record

    def __unicode__(self):
        return '%s( %s )' % (self.__class__.__name__, str(self._target_keys))


class FieldMerger(Filter):
    """ Filter that merges a given set of fields using a supplied merge_func.

        Takes a mapping (dictionary of new_column:(from_col1,from_col2))

        FieldMerger({"bacon": ("spam", "eggs")}, operator.add) creates a new
        column bacon that is the result of spam+eggs
    """

    def __init__(self, mapping, merge_func):
        super(FieldMerger, self).__init__()
        self._field_mapping = mapping
        self._merge_func = merge_func

    def process_record(self, record):
        for to_col,from_cols in self._field_mapping.iteritems():
            values = [record.pop(col, None) for col in from_cols]
            record[to_col] = self._merge_func(*values)
        return record

    def __unicode__(self):
        return '%s( %s, %s )' % (self.__class__.__name__,
                                 str(self._field_mapping),
                                 str(self._merge_func))


class FieldAdder(Filter):
    """ Filter that adds a new field.

        Takes a name for the new field and a value, field_value can be an
        iterable, a function, or a static value.

        from itertools import count
        FieldAdder('id', count)
        
        would yield a new column named id that uses the itertools count iterable
        to create sequentially numbered ids.
    """

    def __init__(self, field_name, field_value):
        super(FieldAdder, self).__init__()
        self._field_name = field_name
        try:
            self._field_value = iter(field_value).next
        except TypeError:
            self._field_value = field_value

    def process_record(self, record):
        if callable(self._field_value):
            record[self._field_name] = self._field_value()
        else:
            record[self._field_name] = self._field_value
        return record

    def __unicode__(self):
        return '%s( %s, %s )' % (self.__class__.__name__, self._field_name,
                             str(self._field_value))


class Splitter(Filter):
    """ Filter that splits nested data into different paths.

        Takes a dictionary of keys and a series of filters to run against the
        associated dictionaries.

        {'person': {'firstname': 'James', 'lastname': 'Turk'},
         'phones': [{'phone': '222-222-2222'}, {'phone': '335-333-3321'}]
        }
    """

    def __init__(self, split_mapping):
        super(Splitter, self).__init__()
        self._split_mapping = split_mapping

    def process_record(self, record):
        for key, filters in self._split_mapping.iteritems():

            subrecord = record[key]

            # if a dict, use process_record directly
            if isinstance(subrecord, dict):
                for filter in filters:
                    subrecord = filter.process_record(subrecord)

            # if a list or tuple, use __call__
            elif isinstance(subrecord, (list, tuple)):
                for filter in filters:
                    subrecord = filter(subrecord)
                subrecord = [r for r in subrecord]  # unchain generators

            # place back from whence it came
            record[key] = subrecord
        return record


class Flattener(Filter):
    """ Collapse a set of similar dictionaries into a list.
    
        Takes a dictionary of keys and flattens the key names:
        
        addresses = [{'addresses': [{'address': {'state':'NC', 'street':'146 shirley drive'}},
                            {'address': {'state':'NY', 'street':'3000 Winton Rd'}}]}]
        flattener = Flattener(['addresses'])
    """
        
    
    def __init__(self):
        super(Flattener, self).__init__()
    
    '''def process_field(self, item):
        # create a list of dictionaries with concatenated keys
        retlist = []
        for subitem in item:
            newitem = {}
            for key1,subdict in subitem.iteritems():
                for key2,value in subdict.iteritems():
                    newitem[key1+'_'+key2] = value
            retlist.append(newitem)
        return retlist
    '''
    
    def process_record(self, record):
        return utils.flatten(record)
    

###########################
## Commonly Used Filters ##
###########################

class PhoneNumberCleaner(FieldFilter):
    """ Filter that cleans phone numbers to match a given format.

        Takes a list of target keys and an optional phone # format that has
        10 %s placeholders.

        PhoneNumberCleaner( ('phone','fax'), number_format='%s%s%s-%s%s%s-%s%s%s%s')
        would format the phone & fax columns to 555-123-4567 format.
    """
    def __init__(self, keys, number_format='%s%s%s.%s%s%s.%s%s%s%s'):
        import re
        super(PhoneNumberCleaner, self).__init__(keys)
        self._number_format = number_format
        self._num_re = re.compile('\d')

    def process_field(self, item):
        nums = self._num_re.findall(item)
        if len(nums) == 10:
            item = self._number_format % tuple(nums)
        return item
