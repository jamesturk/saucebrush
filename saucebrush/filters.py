"""
    Saucebrush Filters are callables that take a Saucebrush source and yield
    back filtered records.

    The Filter, YieldFilter, and FieldFilter abstract base types are provided
    for convenience.  Derived classes only need to implement process_record
    (or process_field for FieldFilter).
"""

from saucebrush import utils
import re
import time

######################
## Abstract Filters ##
######################

class Filter(object):
    """ ABC for filters that operate on records.

        All derived filters must provide a process_record(self, record) that
        takes a single record (python dictionary) and returns a result.
    """

    def process_record(self, record):
        """ Abstract method to be overridden.

            Called with a single record, should return modified record.
        """
        raise NotImplementedError('process_record not defined in ' +
                                  self.__class__.__name__)

    def reject_record(self, record, message):
        recipe = getattr(self, '_recipe')
        if recipe:
            recipe.reject_record(record, message)

    def attach(self, source, recipe=None):
        self._recipe = recipe
        for record in source:
            result = self.process_record(record)
            if result is not None:
                yield result


class YieldFilter(Filter):
    """ ABC for defining filters where process_record yields.

        If process_record cannot return exactly one result for every record
        it is passed, it should yield back as many records as needed and the
        filter must derive from YieldFilter.
    """

    def attach(self, source, recipe=None):
        self._recipe = recipe
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
        self._target_keys = utils.str_or_list(keys)

    def process_record(self, record):
        """ Calls process_field on all keys passed to __init__. """

        for key in self._target_keys:
            try:
                item = record[key]
                record[key] = self.process_field(item)
            except KeyError:
                # probably want to have a boolean to flag missing fields
                pass
        return record

    def process_field(self, item):
        """ Given a value, return the value that it should be replaced with. """

        raise NotImplementedError('process_field not defined in ' +
                                  self.__class__.__name__)

    def __unicode__(self):
        return '%s( %s )' % (self.__class__.__name__, str(self._target_keys))

class ConditionalFilter(YieldFilter):
    """ ABC for filters that only pass through records meeting a condition.

        All derived filters must provide a test_record(self, record) that
        returns True or False -- True indicating that the record should be
        passed through, and False preventing pass through.

        If validator is True then raises a ValidationError instead of
        silently dropping records that fail test_record.
    """

    validator = False

    def process_record(self, record):
        """ Yields all records for which self.test_record is true """

        if self.test_record(record):
            yield record
        elif self.validator:
            raise ValidationError(record)

    def test_record(self, record):
        """ Given a record, return True iff it should be passed on """
        raise NotImplementedError('test_record not defined in ' +
                                  self.__class__.__name__)

class ValidationError(Exception):
    def __init__(self, record):
        super(ValidationError, self).__init__(repr(record))
        self.record = record

def _dotted_get(d, path):
    """
        utility function for SubrecordFilter

        dives into a complex nested dictionary with paths like a.b.c
    """
    if path:
        key_pieces = path.split('.', 1)
        piece = d[key_pieces[0]]
        if isinstance(piece, (tuple, list)):
            return [_dotted_get(i, '.'.join(key_pieces[1:])) for i in piece]
        elif isinstance(piece, (dict)):
            return _dotted_get(piece, '.'.join(key_pieces[1:]))
    else:
        return d

class SubrecordFilter(Filter):
    """ Filter that calls another filter on subrecord(s) of a record

        Takes a dotted path (eg. a.b.c) and instantiated filter and runs that
        filter on all subrecords found at the path.
    """

    def __init__(self, field_path, filter_):
        #if '.' in field_path:
        #    self.field_path, self.key = field_path.rsplit('.', 1)
        #else:
        #    self.field_path = None
        #    self.key = field_path
        self.field_path = field_path
        self.filter = filter_

    def process_record(self, record):
        #if self.field_path:
        subrecord = _dotted_get(record, self.field_path)
        if isinstance(subrecord, (tuple, list)):
            for p in subrecord:
                self.filter.process_record(p)
        else:
            self.filter.process_record(subrecord)
        return record

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
        return '%s( %s, %s )' % (self.__class__.__name__,
                                 str(self._target_keys), str(self._filter_func))


class FieldRemover(Filter):
    """ Filter that removes a given set of fields.

        FieldRemover(('spam', 'eggs')) removes the spam and eggs fields from
        every record filtered.
    """

    def __init__(self, keys):
        super(FieldRemover, self).__init__()
        self._target_keys = utils.str_or_list(keys)

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

    def __init__(self, mapping, merge_func, keep_fields=False):
        super(FieldMerger, self).__init__()
        self._field_mapping = mapping
        self._merge_func = merge_func
        self._keep_fields = keep_fields

    def process_record(self, record):
        for to_col, from_cols in self._field_mapping.iteritems():
            if self._keep_fields:
                values = [record.get(col, None) for col in from_cols]
            else:
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

    def __init__(self, field_name, field_value, replace=True):
        super(FieldAdder, self).__init__()
        self._field_name = field_name
        self._field_value = field_value
        if hasattr(self._field_value, '__iter__'):
            self._field_value = iter(self._field_value).next
        self._replace = replace

    def process_record(self, record):
        if self._field_name not in record or self._replace:
            if callable(self._field_value):
                record[self._field_name] = self._field_value()
            else:
                record[self._field_name] = self._field_value
        return record

    def __unicode__(self):
        return '%s( %s, %s )' % (self.__class__.__name__, self._field_name,
                             str(self._field_value))

class FieldCopier(Filter):
    """ Filter that copies one field to another.

        Takes a dictionary mapping destination keys to source keys.

    """
    def __init__(self, copy_mapping):
        super(FieldCopier, self).__init__()
        self._copy_mapping = copy_mapping

    def process_record(self, record):
        # mapping is dest:source
        for dest, source in self._copy_mapping.iteritems():
            record[dest] = record[source]
        return record

class FieldRenamer(Filter):
    """ Filter that renames one field to another.

        Takes a dictionary mapping destination keys to source keys.
    """
    def __init__(self, rename_mapping):
        super(FieldRenamer, self).__init__()
        self._rename_mapping = rename_mapping

    def process_record(self, record):
        # mapping is dest:source
        for dest, source in self._rename_mapping.iteritems():
            record[dest] = record.pop(source)
        return record

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

            # if the key doesn't exist -- move on to next key
            try:
                subrecord = record[key]
            except KeyError:
                continue

            # if a dict, use process_record directly
            if isinstance(subrecord, dict):
                for filter_ in filters:
                    subrecord = filter_.process_record(subrecord)

            # if a list or tuple, use attach
            elif isinstance(subrecord, (list, tuple)):
                for filter_ in filters:
                    subrecord = filter_.attach(subrecord, recipe=self._recipe)
                subrecord = [r for r in subrecord]  # unchain generators

            # place back from whence it came
            record[key] = subrecord
        return record


class Flattener(FieldFilter):
    """ Collapse a set of similar dictionaries into a list.

        Takes a dictionary of keys and flattens the key names:

        addresses = [{'addresses': [{'address': {'state':'NC', 'street':'146 shirley drive'}},
                            {'address': {'state':'NY', 'street':'3000 Winton Rd'}}]}]
        flattener = Flattener(['addresses'])

        would yield:

        {'addresses': [{'state': 'NC', 'street': '146 shirley drive'},
                       {'state': 'NY', 'street': '3000 Winton Rd'}]}
    """
    def __init__(self, keys):
        super(Flattener, self).__init__(keys)

    def process_field(self, item):
        result = []
        for d in item:
            rec = {}
            for values in d.values():
                rec.update(values)
            result.append(rec)
        return result


class DictFlattener(Filter):
    def __init__(self, keys, separator='_'):
        super(DictFlattener, self).__init__()
        self._keys = utils.str_or_list(keys)
        self._separator = separator

    def process_record(self, record):
        return utils.flatten(record, keys=self._keys, separator=self._separator)


class Unique(ConditionalFilter):
    """ Filter that ensures that all records passing through are unique.
    """

    def __init__(self):
        super(Unique, self).__init__()
        self._seen = set()

    def test_record(self, record):
        record_hash = hash(repr(record))
        if record_hash not in self._seen:
            self._seen.add(record_hash)
            return True
        else:
            return False

class UniqueValidator(Unique):
    validator = True


class UniqueID(ConditionalFilter):
    """ Filter that ensures that all records through have a unique ID.

        Takes the name of an ID field, or multiple field names in the case
        of a composite ID.
    """

    def __init__(self, field='id', *args):
        super(UniqueID, self).__init__()
        self._seen = set()
        self._id_fields = [field]
        self._id_fields.extend(args)

    def test_record(self, record):
        id_hash = hash(repr([record[key] for key in self._id_fields]))
        if id_hash not in self._seen:
            self._seen.add(id_hash)
            return True
        else:
            return False

class UniqueIDValidator(UniqueID):
    validator = True


class UnicodeFilter(Filter):
    """ Convert all str elements in the record to Unicode.
    """

    def __init__(self, encoding='utf-8', errors='ignore'):
        super(UnicodeFilter, self).__init__()
        self._encoding = encoding
        self._errors = errors

    def process_record(self, record):
        for key, value in record.iteritems():
            if isinstance(value, str):
                record[key] = unicode(value, self._encoding, self._errors)
            elif isinstance(value, unicode):
                record[key] = value.decode(self._encoding, self._errors)
        return record

class StringFilter(Filter):

    def __init__(self, encoding='utf-8', errors='ignore'):
        super(StringFilter, self).__init__()
        self._encoding = encoding
        self._errors = errors

    def process_record(self, record):
        for key, value in record.iteritems():
            if isinstance(value, unicode):
                record[key] = value.encode(self._encoding, self._errors)
        return record


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
        super(PhoneNumberCleaner, self).__init__(keys)
        self._number_format = number_format
        self._num_re = re.compile('\d')

    def process_field(self, item):
        nums = self._num_re.findall(item)
        if len(nums) == 10:
            item = self._number_format % tuple(nums)
        return item

class DateCleaner(FieldFilter):
    """ Filter that cleans dates to match a given format.

        Takes a list of target keys and to and from formats in strftime format.
    """
    def __init__(self, keys, from_format, to_format):
        super(DateCleaner, self).__init__(keys)
        self._from_format = from_format
        self._to_format = to_format

    def process_field(self, item):
        return time.strftime(self._to_format,
                             time.strptime(item, self._from_format))

class NameCleaner(Filter):
    """ Filter that splits names into a first, last, and middle name field.

        Takes a list of target keys.

        NameCleaner( ('name', ), nomatch_name='raw_name')
        would attempt to split 'name' into firstname, middlename, lastname,
        and suffix columns, and if it did not fit would place it in raw_name
    """

    # first middle? last suffix?
    FIRST_LAST = re.compile('''^\s*(?:(?P<firstname>\w+)(?:\.?)
                                \s+(?:(?P<middlename>\w+)\.?\s+)?
                                (?P<lastname>[A-Za-z'-]+))
                                (?:\s+(?P<suffix>JR\.?|II|III|IV))?
                                \s*$''', re.VERBOSE | re.IGNORECASE)

    # last, first middle? suffix?
    LAST_FIRST = re.compile('''^\s*(?:(?P<lastname>[A-Za-z'-]+),
                                \s+(?P<firstname>\w+)(?:\.?)
                                (?:\s+(?P<middlename>\w+)\.?)?)
                                (?:\s+(?P<suffix>JR\.?|II|III|IV))?
                                \s*$''', re.VERBOSE | re.IGNORECASE)

    def __init__(self, keys, prefix='', formats=None, nomatch_name=None):
        super(NameCleaner, self).__init__()
        self._keys = utils.str_or_list(keys)
        self._name_prefix = prefix
        self._nomatch_name = nomatch_name
        if formats:
            self._name_formats = formats
        else:
            self._name_formats = [self.FIRST_LAST, self.LAST_FIRST]

    def process_record(self, record):
        # run for each key (not using a FieldFilter due to multi-field output)
        for key in self._keys:
            name = record[key]

            # check if key matches any formats
            for format in self._name_formats:
                match = format.match(name)

                # if there is a match, remove original name and add pieces
                if match:
                    record.pop(key)
                    for k,v in match.groupdict().iteritems():
                        record[self._name_prefix + k] = v
                    break

            # if there is no match, move name into nomatch_name
            else:
                if self._nomatch_name:
                    record.pop(key)
                    record[self._nomatch_name] = name

        return record
