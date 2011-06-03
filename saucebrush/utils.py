import urllib2
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


def string_dig(element, separator=''):
    """
        Dig into BeautifulSoup HTML elements looking for inner strings.

        If element resembled: <p><b>test</b><em>test</em></p>
        then string_dig(element, '~') would return test~test
    """
    if element.string:
        return element.string
    else:
        return separator.join([string_dig(child)
                            for child in element.findAll(True)])


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
        for key, value in item.iteritems():
            if (not keys) or (key in keys):
                retval.update(flatten(value, prefix + key, separator, keys))
            else:
                retval[prefix + key] = value
        return retval
    #elif isinstance(item, (tuple, list)):
    #    return {prefix: [flatten(i, prefix, separator, keys) for i in item]}
    else:
        print item, prefix
        return {prefix: item}
    
def str_or_list(obj):
    if isinstance(obj, str):
        return [obj]
    else:
        return obj

#
# utility classes
#

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
        import os
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
        resp = urllib2.urlopen(self._url)
        for line in resp:
            yield line.rstrip()
        resp.close()