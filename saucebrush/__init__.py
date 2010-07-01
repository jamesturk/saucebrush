"""
    Saucebrush is a data loading & manipulation framework written in python.
"""

import filters, emitters, sources, utils


class SaucebrushError(Exception):
    pass


class OvercookedError(Exception):
    """
    Exception for trying to operate on a Recipe that has been finished.
    """
    pass


class Recipe(object):

    def __init__(self, *filter_args, **kwargs):
        self.finished = False

        self.filters = []
        for filter in filter_args:
            if hasattr(filter, 'filters'):
                self.filters.extend(filter.filters)
            else:
                self.filters.append(filter)

        self.error_stream = kwargs.get('error_stream')
        if self.error_stream and not isinstance(self.error_stream, Recipe):
            if isinstance(self.error_stream, filters.Filter):
                self.error_stream = Recipe(self.error_stream)
            elif hasattr(self.error_stream, '__iter__'):
                self.error_stream = Recipe(*self.error_stream)
            else:
                raise SaucebrushError('error_stream must be either a filter'
                                      ' or an iterable of filters')

    def reject_record(self, record, exception):
        if self.error_stream:
            self.error_stream.run([{'record': record,
                                    'exception': repr(exception)}])

    def run(self, source):
        if self.finished:
            raise OvercookedError('run() called on finished recipe')

        # connect datapath
        data = source
        for filter_ in self.filters:
            data = filter_.attach(data, recipe=self)

        # actually run the data through (causes iterators to actually be called)
        for record in data:
            pass

    def done(self):
        if self.finished:
            raise OvercookedError('done() called on finished recipe')

        self.finished = True

        if self.error_stream:
            self.error_stream.done()

        # try and call done() on all filters
        for filter_ in self.filters:
            try:
                filter_.done()
            except AttributeError:
                pass    # don't care if there isn't a done method


def run_recipe(source, *filter_args, **kwargs):
    """ Process data, taking it from a source and applying any number of filters
    """

    r = Recipe(*filter_args, **kwargs)
    r.run(source)
    r.done()
    return r
