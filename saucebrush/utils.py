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
    dbmodel = get_model(app_label, model_name)


def string_dig(element, joiner=''):
    """
        Dig into BeautifulSoup HTML elements looking for inner strings.

        If element resembled: <p><b>test</b><em>test</em></p>
        then string_dig(element, '~') would return test~test
    """
    if element.string:
        return element.string
    else:
        return joiner.join([string_dig(child) for child in element.findAll(True)])


def dotted_key_lookup(dict_, dotted_key, default=KeyError, separator='.'):
    """
        Do a lookup within dict_ by the various elements of dotted_key.

        Optionally specifiy a default to return if key does not exist (similar
        to default

        >>> d = {'a': {'b': {'c': 3} } }
        >>> dotted_key_lookup(d, 'a.b.c')
        3
        >>> dotted_key_lookup(d, 'a.z', -1)
        -1
        >>> dotted_key_lookup(d, 'a|b|c', separator='|')
        3
        >>> dotted_key_lookup(d, '
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
