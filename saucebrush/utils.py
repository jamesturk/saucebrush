import collections
import os

try:
    from urllib.request import urlopen  # attemp py3 first
except ImportError:
    from urllib2 import urlopen         # fallback to py2

"""
    General utilities used within saucebrush that may be useful elsewhere.
"""

def get_django_model(dj_settings, app_label, model_name):
    """
        Get a django model given a settings file, app label, and model name.
    """

    from django.conf import settings
    if not settings.configured:
        settings.configure(DATABASE_ENGINE=dj_settings.DATABASE_ENGINE,
                           DATABASE_NAME=dj_settings.DATABASE_NAME,
                           DATABASE_USER=dj_settings.DATABASE_USER,
                           DATABASE_PASSWORD=dj_settings.DATABASE_PASSWORD,
                           DATABASE_HOST=dj_settings.DATABASE_HOST,
                           INSTALLED_APPS=dj_settings.INSTALLED_APPS)
    from django.db.models import get_model
    return get_model(app_label, model_name)

def flatten(item, prefix='', separator='_', keys=None):
    """
        Flatten nested dictionary into one with its keys concatenated together.

        >>> flatten({'a':1, 'b':{'c':2}, 'd':[{'e':{'r':7}}, {'e':5}],
                    'f':{'g':{'h':6}}})
        {'a': 1, 'b_c': 2, 'd': [{'e_r': 7}, {'e': 5}], 'f_g_h': 6}
    """

    # update dictionaries recursively

    if isinstance(item, dict):
        # don't prepend a leading _
        if prefix != '':
            prefix += separator
        retval = {}
        for key, value in item.items():
            if (not keys) or (key in keys):
                retval.update(flatten(value, prefix + key, separator, keys))
            else:
                retval[prefix + key] = value
        return retval
    #elif isinstance(item, (tuple, list)):
    #    return {prefix: [flatten(i, prefix, separator, keys) for i in item]}
    else:
        return {prefix: item}

def str_or_list(obj):
    if isinstance(obj, str):
        return [obj]
    else:
        return obj

#
# utility classes
#

class FallbackCounter(collections.defaultdict):
    """ Python 2.6 does not have collections.Counter.
        This is class that does the basics of what we need from Counter.
    """

    def __init__(self, *args, **kwargs):
        super(FallbackCounter, self).__init__(int)

    def most_common(n=None):

        l = sorted(self.items(),
                cmp=lambda x,y: cmp(x[1], y[1]))

        if n is not None:
            l = l[:n]

        return l

class Files(object):
    """ Iterate over multiple files as a single file. Pass the paths of the
        files as arguments to the class constructor:

            for line in Files('/path/to/file/a', '/path/to/file/b'):
                pass
    """

    def __init__(self, *args):
        self.paths = []
        for arg in args:
            self.add(arg)
        self.file_open_callback = None

    def add(self, path):
        self.paths.append(path)

    def __iter__(self):
        return self.linereader()

    def linereader(self):
        for path in iter(self.paths):
            if os.path.exists(path):
                if self.file_open_callback:
                    self.file_open_callback(path)
                f = open(path)
                for line in f:
                    yield line
                f.close()

class RemoteFile(object):
    """ Stream data from a remote file.

        :param url: URL to remote file
    """

    def __init__(self, url):
        self._url = url

    def __iter__(self):
        resp = urlopen(self._url)
        for line in resp:
            yield line.rstrip()
        resp.close()

class ZippedFiles(object):
    """ unpack a zipped collection of files on init.

        Takes a string with file location or zipfile.ZipFile object

        Best to wrap this in a Files() object, if the goal is to have a
        linereader, as this only returns filelike objects.

        if using a ZipFile object, make sure to set mode to 'a' or 'w' in order
        to use the add() function. 
    """
    def __init__(self, zippedfile):
        import zipfile
        if type(zippedfile) == str:
            self._zipfile = zipfile.ZipFile(zippedfile,'a')
        else:
            self._zipfile = zippedfile
        self.paths = self._zipfile.namelist()
        self.file_open_callback = None

    def __iter__(self):
        return self.filereader()

    def add(self, path, dirname=None, arcname=None):
        path_base = os.path.basename(path)
        if dirname:
            arcname = os.path.join(dirname,path_base)
        if not arcname:
            arcname = path_base
        self._zipfile.write(path,arcname)
        self.paths.append(path)

    def filereader(self):
        for path in iter(self.paths):
            if self.file_open_callback:
                self.file_open_callback(path)
            yield self._zipfile.open(path)
