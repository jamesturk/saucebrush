"""
    Saucebrush data sources, convert data in some format into python dicts.

    All sources must implement the iterable interface and return python
    dictionaries.
"""

import string
from saucebrush import utils

class CSVSource(object):
    """ Saucebrush source for reading from CSV files.

        Takes an open csvfile, an optional set of fieldnames and optional number
        of rows to skip.

        CSVSource(open('test.csv')) will read a csvfile, using the first row as
        the field names.

        CSVSource(open('test.csv'), ('name', 'phone', 'address'), 1) will read
        in a CSV file and treat the three columns as name, phone, and address,
        ignoring the first row (presumed to be column names).
    """

    def __init__(self, csvfile, fieldnames=None, skiprows=0):
        import csv
        self._dictreader = csv.DictReader(csvfile, fieldnames)
        for _ in xrange(skiprows):
            self._dictreader.next()

    def __iter__(self):
        return self._dictreader


class FixedWidthFileSource(object):
    """ Saucebrush source for reading from fixed width field files.

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

    def next(self):
        line = self._fwfile.next()
        record = {}
        for name, range_ in self._fields_dict.iteritems():
            record[name] = line[range[0]:range_[1]].rstrip(self._fillchars)
        return record


class HtmlTableSource(object):
    """ Saucebrush source for reading data from an HTML table.

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
        from BeautifulSoup import BeautifulSoup
        soup = BeautifulSoup(htmlfile.read())
        if isinstance(id_or_num, int):
            table = soup.findAll('table')[id_or_num]
        elif isinstance(id_or_num, str):
            table = soup.find('table', id=id_or_num)

        # skip the necessary number of rows
        self._rows = table.findAll('tr')[skiprows:]

        # determine the fieldnames
        if not fieldnames:
            self._fieldnames = [td.string
                                for td in self._rows[0].findAll(('td','th'))]
        else:
            self._fieldnames = fieldnames

    def process_tr(self):
        for row in self._rows:
            strings = [utils.string_dig(td) for td in row.findAll('td')]
            yield dict(zip(self._fieldnames, strings))

    def __iter__(self):
        return self.process_tr()


class DjangoModelSource(object):
    """ Saucebrush source for reading data from django models.

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
        self._data = dbmodel.objects.values(*[f.name
                                              for f in dbmodel._meta.fields])

    def __iter__(self):
        return iter(self._data)


class MongoDBSource(object):
    """ Source for reading from a MongoDB database.
    
        The record dict is populated with records matching the spec
        from the specified database and collection.
    """
    def __init__(self, database, collection, spec=None, host='localhost', port=27017, conn=None):
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


class SqliteSource(object):
    """ Source that reads from a sqlite database.

        The record dict is populated with the results from the
        query argument. If given, args will be passed to the query
        when executed.    
    """

    def __init__(self, dbpath, query, args=None, conn_params=None):
        self._dbpath = dbpath
        self._query = query
        self._args = args or []
        self._conn_params = conn_params or []

    def _process_query(self):

        import sqlite3
        
        def dict_factory(cursor, row):
            d = { }
            for idx, col in enumerate(cursor.description):
                d[col[0]] = row[idx]
            return d

        conn = sqlite3.connect(self._dbpath)
        conn.row_factory = dict_factory

        if self._conn_params:
            for param, value in self._conn_params.iteritems():
                setattr(conn, param, value)

        cursor = conn.cursor()

        for row in cursor.execute(self._query, self._args):
            yield row

        cursor.close()
        conn.close()

    def __iter__(self):
        return self._process_query()
