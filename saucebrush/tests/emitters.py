import unittest
from cStringIO import StringIO
from saucebrush.emitters import DebugEmitter, CSVEmitter, CountEmitter

class EmitterTestCase(unittest.TestCase):

    def setUp(self):
        self.output = StringIO()

    def test_debug_emitter(self):
        de = DebugEmitter(self.output)
        data = de.attach([1,2,3])
        for _ in data:
            pass
        self.assertEquals(self.output.getvalue(), '1\n2\n3\n')

    def test_csv_emitter(self):
        ce = CSVEmitter(self.output, ('x','y','z'))
        data = ce.attach([{'x':1,'y':2,'z':3}, {'x':5, 'y':5, 'z':5}])
        for _ in data:
            pass
        self.assertEquals(self.output.getvalue(), 'x,y,z\r\n1,2,3\r\n5,5,5\r\n')
    
    def test_count_emitter(self):
        ce = CountEmitter(every=10, outfile=self.output, format="%s records\n")
        data = ce.attach([1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22])
        for _ in data:
            pass
        self.assertEquals(self.output.getvalue(), '10 records\n20 records\n')
        ce.done()
        self.assertEquals(self.output.getvalue(), '10 records\n20 records\n22 records\n')

if __name__ == '__main__':
    unittest.main()
