"""
    Saucebrush data sources, convert data in some format into python dicts.

    All sources must implement the iterable interface and return python
    dictionaries.
"""
from __future__ import unicode_literals
import string

from saucebrush import utils


class CSVSource(object):
    """Saucebrush source for reading from CSV files.

    Takes an open csvfile, an optional set of fieldnames and optional number
    of rows to skip.

    CSVSource(open('test.csv')) will read a csvfile, using the first row as
    the field names.

    CSVSource(open('test.csv'), ('name', 'phone', 'address'), 1) will read
    in a CSV file and treat the three columns as name, phone, and address,
    ignoring the first row (presumed to be column names).
    """

    def __init__(self, csvfile, fieldnames=None, skiprows=0, **kwargs):
        import csv

        self._dictreader = csv.DictReader(csvfile, fieldnames, **kwargs)
        for _ in range(skiprows):
            next(self._dictreader)

    def __iter__(self):
        return self._dictreader


class FixedWidthFileSource(object):
    """Saucebrush source for reading from fixed width field files.

    FixedWidthFileSource expects an open fixed width file and a tuple
    of fields with their lengths.  There is also an optional fillchars
    command that is the filler characters to strip from the end of each
    field. (defaults to whitespace)

    FixedWidthFileSource(open('testfile'), (('name',30), ('phone',12)))
    will read in a fixed width file where the first 30 characters of each
    line are part of a name and the characters 31-42 are a phone number.
    """

    def __init__(self, fwfile, fields, fillchars=string.whitespace):
        self._fwfile = fwfile
        self._fields_dict = {}
        self._fillchars = fillchars
        from_offset = 0
        to_offset = 0
        for field, size in fields:
            to_offset += size
            self._fields_dict[field] = (from_offset, to_offset)
            from_offset += size

    def __iter__(self):
        return self

    def __next__(self):
        line = next(self._fwfile)
        record = {}
        for name, range_ in self._fields_dict.items():
            record[name] = line[range_[0] : range_[1]].rstrip(self._fillchars)
        return record

    def next(self):
        """Keep Python 2 next() method that defers to __next__()."""
        return self.__next__()


class HtmlTableSource(object):
    """Saucebrush source for reading data from an HTML table.

    HtmlTableSource expects an open html file, the id of the table or a
    number indicating which table on the page to use, an optional fieldnames
    tuple, and an optional number of rows to skip.

    HtmlTableSource(open('test.html'), 0) opens the first HTML table and
    uses the first row as the names of the columns.

    HtmlTableSource(open('test.html'), 'people', ('name','phone'), 1) opens
    the HTML table with an id of 'people' and names the two columns
    name and phone, skipping the first row where alternate names are
    stored.
    """

    def __init__(self, htmlfile, id_or_num, fieldnames=None, skiprows=0):

        # extract the table
        from lxml.html import parse

        doc = parse(htmlfile).getroot()
        if isinstance(id_or_num, int):
            table = doc.cssselect("table")[id_or_num]
        else:
            table = doc.cssselect("table#%s" % id_or_num)

        table = table[0]  # get the first table

        # skip the necessary number of rows
        self._rows = table.cssselect("tr")[skiprows:]

        # determine the fieldnames
        if not fieldnames:
            self._fieldnames = [
                td.text_content() for td in self._rows[0].cssselect("td, th")
            ]
            skiprows += 1
        else:
            self._fieldnames = fieldnames

        # skip the necessary number of rows
        self._rows = table.cssselect("tr")[skiprows:]

    def process_tr(self):
        for row in self._rows:
            strings = [td.text_content() for td in row.cssselect("td")]
            yield dict(zip(self._fieldnames, strings))

    def __iter__(self):
        return self.process_tr()


class DjangoModelSource(object):
    """Saucebrush source for reading data from django models.

    DjangoModelSource expects a django settings file, app label, and model
    name.  The resulting records contain all columns in the table for the
    specified model.

    DjangoModelSource('settings.py', 'phonebook', 'friend') would read all
    friends from the friend model in the phonebook app described in
    settings.py.
    """

    def __init__(self, dj_settings, app_label, model_name):
        dbmodel = utils.get_django_model(dj_settings, app_label, model_name)

        # only get values defined in model (no extra fields from custom manager)
        self._data = dbmodel.objects.values(*[f.name for f in dbmodel._meta.fields])

    def __iter__(self):
        return iter(self._data)


class MongoDBSource(object):
    """Source for reading from a MongoDB database.

    The record dict is populated with records matching the spec
    from the specified database and collection.
    """

    def __init__(
        self, database, collection, spec=None, host="localhost", port=27017, conn=None
    ):
        if not conn:
            from pymongo.connection import Connection

            conn = Connection(host, port)
        self.collection = conn[database][collection]
        self.spec = spec

    def __iter__(self):
        return self._find_spec()

    def _find_spec(self):
        for doc in self.collection.find(self.spec):
            yield dict(doc)


# dict_factory for sqlite source
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


class SqliteSource(object):
    """Source that reads from a sqlite database.

    The record dict is populated with the results from the
    query argument. If given, args will be passed to the query
    when executed.
    """

    def __init__(self, dbpath, query, args=None, conn_params=None):

        import sqlite3

        self._dbpath = dbpath
        self._query = query
        self._args = args or []
        self._conn_params = conn_params or []

        # setup connection
        self._conn = sqlite3.connect(self._dbpath)
        self._conn.row_factory = dict_factory
        if self._conn_params:
            for param, value in self._conn_params.items():
                setattr(self._conn, param, value)

    def _process_query(self):

        cursor = self._conn.cursor()

        for row in cursor.execute(self._query, self._args):
            yield row

        cursor.close()

    def __iter__(self):
        return self._process_query()

    def done(self):
        self._conn.close()


class FileSource(object):
    """Base class for sources which read from one or more files.

    Takes as input a file-like, a file path, a list of file-likes,
    or a list of file paths.
    """

    def __init__(self, input):
        self._input = input

    def __iter__(self):
        # This method would be a lot cleaner with the proposed
        # 'yield from' expression (PEP 380)
        if hasattr(self._input, "__read__") or hasattr(self._input, "read"):
            for record in self._process_file(self._input):
                yield record
        elif isinstance(self._input, str):
            with open(self._input) as f:
                for record in self._process_file(f):
                    yield record
        elif hasattr(self._input, "__iter__"):
            for el in self._input:
                if isinstance(el, str):
                    with open(el) as f:
                        for record in self._process_file(f):
                            yield record
                elif hasattr(el, "__read__") or hasattr(el, "read"):
                    for record in self._process_file(f):
                        yield record

    def _process_file(self, file):
        raise NotImplementedError(
            "Descendants of FileSource should implement"
            " a custom _process_file method."
        )


class JSONSource(FileSource):
    """Source for reading from JSON files.

    When processing JSON files, if the top-level object is a list, will
    yield each member separately. Otherwise, yields the top-level
    object.
    """

    def _process_file(self, f):

        import json

        obj = json.load(f)

        # If the top-level JSON object in the file is a list
        # then yield each element separately; otherwise, yield
        # the top-level object.
        if isinstance(obj, list):
            for record in obj:
                yield record
        else:
            yield obj


class XMLSource(FileSource):
    """Source for reading from XML files. Use with the same kind of caution
    that you use to approach anything written in XML.

    When processing XML files, if the top-level object is a list, will
    yield each member separately, unless the dotted path to a list is
    included. you can also do this with a SubrecordFilter, but XML is
    almost never going to be useful at the top level.
    """

    def __init__(self, input, node_path=None, attr_prefix="ATTR_", postprocessor=None):
        super(XMLSource, self).__init__(input)
        self.node_list = node_path.split(".")
        self.attr_prefix = attr_prefix
        self.postprocessor = postprocessor

    def _process_file(self, f, attr_prefix="ATTR_"):
        """xmltodict can either return attributes of nodes as prefixed fields
        (prefixes to avoid key collisions), or ignore them altogether.

        set attr prefix to whatever you want. Setting it to False ignores
        attributes.
        """

        import xmltodict

        if self.postprocessor:
            obj = xmltodict.parse(
                f, attr_prefix=self.attr_prefix, postprocessor=self.postprocessor
            )
        else:
            obj = xmltodict.parse(f, attr_prefix=self.attr_prefix)

        # If node list was given, walk down the tree

        if self.node_list:
            for node in self.node_list:
                obj = obj[node]

        # If the top-level XML object in the file is a list
        # then yield each element separately; otherwise, yield
        # the top-level object.
        if isinstance(obj, list):
            for record in obj:
                yield record
        else:
            yield obj
