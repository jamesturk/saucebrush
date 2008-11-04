import filters, emitters, sources, utils

def run_recipe(source, *filters):
    # connect datapath
    data = source
    for filter in filters:
        data = filter(data)

    # actually run the data through (causes iterators to actually be called)
    for record in data:
        pass

    # try and call done() on all filters
    for filter in filters:
        try:
            filter.done()
        except AttributeError:
            pass    # don't care if there isn't a done method
