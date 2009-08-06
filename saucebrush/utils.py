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

def dotted_key_lookup(dict_, dotted_key, default=KeyError, separator='.'):
    """
        Do a lookup within dict_ by the various elements of dotted_key.

        Optionally specify a default to return if key does not exist (similar
        to default)

        >>> d = {'a': {'b': {'c': 3} } }
        >>> dotted_key_lookup(d, 'a.b.c')
        3
        >>> dotted_key_lookup(d, 'a.z', -1)
        -1
        >>> dotted_key_lookup(d, 'a|b|c', separator='|')
        3
    """
    val = dict_
    try:
        for key in dotted_key.split(separator):
            if isinstance(val, dict):
                val = val[key]
            elif isinstance(val, (list,tuple)):
                val = val[int(key)]
            else:
                val = getattr(val, key)
    except (KeyError, IndexError, AttributeError):
        if default is KeyError:
            raise
        val = default
    return val

def dotted_key_pop(dict_, dotted_key, default=KeyError, separator='.'):
    """
        Delete a value within dict_ by the various elements of dotted_key.
    """
    val = dict_
    try:
        key_parts = dotted_key.split(separator)
        for key in key_parts[:-1]:
            if isinstance(val, dict):
                val = val[key]
            elif isinstance(val, (list,tuple)):
                val = val[int(key)]
            else:
                val = getattr(val, key)

        # now with just the final part of the key
        key = key_parts[-1]
        if isinstance(val, dict):
            retval = val[key]
            del val[key]
        elif isinstance(val, (list,tuple)):
            retval = val[int(key)]
            del val[int(key)]
        else:
            retval = getattr(val, key)
            delattr(val, key)
    except (KeyError, IndexError, AttributeError):
        if default is KeyError:
            raise
        retval = default
    return retval

def dotted_key_set(dict_or_list, dotted_key, value, separator='.'):
    """
        Set a value within dict_ using a dotted_key.
        
        >>> d = {}
        >>> dotted_key_set(d, 'a.b.c', 123}
        >>> d
        {'a': {'b': {'c': 123}}}
    """
    
    # split key into composite parts
    keys = dotted_key.split(separator)
    
    for i,key in enumerate(keys):
        
        # if current location is a dictionary: traverse inward until @ last key
        # set value when last key is reached
        if isinstance(dict_or_list, dict):
            if i == len(keys)-1:
                dict_or_list[key] = value
            else:
                try:
                    dict_or_list = dict_or_list[key]
                except KeyError:
                    break
                
        # if current location is a list: call dotted_key_set on each element
        elif isinstance(dict_or_list, (tuple, list)):
            newkey = separator.join(keys[i:])
            for item in dict_or_list:
                dotted_key_set(item, newkey, value, separator)

#
# utility classes
#

class Files(object):

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