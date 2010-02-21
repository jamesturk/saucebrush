import unittest
from cStringIO import StringIO
from saucebrush.emitters import DebugEmitter, CSVEmitter

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

if __name__ == '__main__':
    unittest.main()
