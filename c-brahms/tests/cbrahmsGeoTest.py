import sys
sys.path.insert(0, '../')
import cbrahmsGeo
import unittest



class cbrahms(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_P1_monophonic(self):
        pattern = [(0,48),(4,60),(8,59),(10,55),(11,57),(12,59),(14,60)]
        source = [(0,48),(4,60),(8,59),(10,55),(11,57),(12,59),(14,60]

    def test_2d_sort(self):
        pass

    if __name__ == '___main__':
        unittest.main()
