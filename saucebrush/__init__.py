"""
    Saucebrush is a data loading & manipulation framework written in python.
"""

import filters, emitters, sources, utils

class Recipe(filters.Filter):

    def __init__(self, *filter_args):
        self._filter_args = filter_args
        self.rejected = []

    def get_filters(self):

        filters = []

        for filter_ in self._filter_args:

            # check to see if this is a filter or a recipe

            if hasattr(filter_, 'get_filters'):
                # load filters from child recipe
                filters.extend(filter_.get_filters())
            else:
                filters.append(filter_)

        return filters

    def reject_record(self):
        self.rejected.append((record, message))

    def run(self, source):

        # load filters
        filters = self.get_filters()

        # connect datapath
        data = source
        for filter_ in filters:
            data = filter_(data, recipe=self)

        # actually run the data through (causes iterators to actually be called)
        for record in data:
            pass

        # try and call done() on all filters
        for filter_ in filters:
            try:
                filter_.done()
            except AttributeError:
                pass    # don't care if there isn't a done method

def run_recipe(source, *filter_args):
    """ Process data, taking it from a source and applying any number of filters
    """

    r = Recipe(*filter_args)
    r.run(source)
    return r
