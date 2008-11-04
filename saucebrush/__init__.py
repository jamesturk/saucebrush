"""
    Saucebrush is a data loading & manipulation framework written in python.
"""

import filters, emitters, sources, utils

def run_recipe(source, *filter_args):
    """ Process data, taking it from a source and applying any number of filters
    """
    
    # connect datapath
    data = source
    for filter_ in filter_args:
        data = filter_(data)

    # actually run the data through (causes iterators to actually be called)
    for record in data:
        pass

    # try and call done() on all filters
    for filter_ in filter_args:
        try:
            filter_.done()
        except AttributeError:
            pass    # don't care if there isn't a done method
