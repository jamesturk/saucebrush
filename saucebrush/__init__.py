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


# experiment with threading - do not use

from threading import Thread as TaskType
from Queue import Queue
from threading import activeCount as active_tasks

# uncomment to use processing instead of threading
#from processing import Process as TaskType
#from processing import Queue
#def active_tasks():
#    from processing import activeChildren
#    return len(activeChildren())


class FilterThread(TaskType):
    __create_count = 0
    
    def __init__(self, filter, data, queue=True):
        super(FilterThread, self).__init__(name='saucebrush-%d' %
                                           FilterThread.__create_count)
        FilterThread.__create_count += 1
        self._filter = filter
        self._data = data
        if queue:
            self._queue = Queue()   # threading or processing Queue
        else:
            self._queue = None
        
    def done(self):
        try:
            self._filter.done()
        except AttributeError:
            pass    # don't care if there isn't a done method

    def run(self):
        try:
            for record in iter(self._data):
                result = self._filter.process_record(record)
                if self._queue:
                    self._queue.put(result)
            if self._queue:
                self._queue.put(None)
        except Exception, e:
            print e
            if self._queue:
                self._queue.put(None)
        print self.getName(), 'exiting.'
    
    def __iter__(self):
        item = True
        while item is not None:
            item = self._queue.get()
            if item is not None:
                yield item

def run_recipe_multitasking(source, *filter_args):
    max_tasks = 5
    tasks = []

    data = source
    for filter_ in filter_args:
        # this task is the next task's data source
        data = FilterThread(filter_, data)
        tasks.append(data)
        
    tasks[-1]._queue = None
        
    # start all threads (no more than max_threads at once)
    tasks_started = 0
    while tasks_started < len(tasks):
        if active_tasks() < max_tasks:
            tasks[tasks_started].start()
            print 'starting task', tasks_started
            tasks_started += 1
    
    # wait for all threads and call done
    for task in tasks:
        print 'joining', task
        task.join()
        print task, 'joined'
        task.done()
