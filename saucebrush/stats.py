from saucebrush.filters import Filter

class StatsFilter(Filter):
    
    def __init__(self, field, test=None):
        self._field = field
        self._test = test if test else lambda x: True
        
    def process_record(self, record):
        if self._test(record):
            self.process_field(record[self._field])
        return record
    
    def process_field(self, record):
        raise NotImplementedError('process_field not defined in ' +
                                  self.__class__.__name__)
    
    def value(self):
        raise NotImplementedError('value not defined in ' +
                                  self.__class__.__name__)

class Sum(StatsFilter):
    
    def __init__(self, field, initial=0, **kwargs):
        super(Sum, self).__init__(field, **kwargs)
        self._value = initial
        
    def process_field(self, item):
        self._value += item or 0
        
    def value(self):
        return self._value

class Average(StatsFilter):
    
    def __init__(self, field, initial=0, **kwargs):
        super(Average, self).__init__(field, **kwargs)
        self._value = initial
        self._count = 0
        
    def process_field(self, item):
        self._value += item or 0
        self._count += 1
        
    def value(self):
        return self._value / self._count