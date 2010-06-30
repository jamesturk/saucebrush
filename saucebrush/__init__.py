"""
    Saucebrush is a data loading & manipulation framework written in python.
"""

import filters, emitters, sources, utils


class Recipe(object):

    def __init__(self, *filter_args, **kwargs):
        self._filter_args = filter_args
        self.rejected = []

        self.error_stream = kwargs.get('error_stream')
        if self.error_stream and not isinstance(self.error_stream, Recipe):
            if isinstance(self.error_stream, filters.Filter):
                self.error_stream = Recipe(self.error_stream)
            elif hasattr(self.error_stream, '__iter__'):
                self.error_stream = Recipe(*self.error_stream)
            else:
                raise ValueError('error_stream must be either a filter'
                                 ' or an iterable of filters')

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

    def reject_record(self, record, message):
        if self.error_stream:
            self.error_stream.run([record])

    def run(self, source):
        # load filters
        filters = self.get_filters()

        # connect datapath
        data = source
        for filter_ in filters:
            data = filter_.attach(data, recipe=self)

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
