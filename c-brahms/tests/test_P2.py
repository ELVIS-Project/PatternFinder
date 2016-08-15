from unittest import TestCase, TestLoader
from vis.analyzers.indexers import noterest, metre
from tests import tools
from functools import partial
import cbrahmsGeo
import midiparser
import music21
import pandas
import pdb


class CBRAHMSTestP2(TestCase):

    def setUp(self):
        # Over the Rainbow query
        self.pattern = [[0,48],[4,60],[8,59],[10,55],[11,57],[12,59],[14,60]]
        self.P2_exact = partial(cbrahmsGeo.P2, mismatch = 0)

    def tearDown(self):
        pass

    def test_automatic_shift_pattern(self):
        shift = [1,1]
        source = tools.shift_pattern(shift, self.pattern)
        expected = [[1,49],[5,61],[9,60],[11,56],[12,58],[13,60],[15,61]]
        self.assertEqual(source, expected)

    def test_P2_pattern_larger_than_source(self):
        """
        Tests P2 with a pattern that is larger than the source. It should return a shift which results in len(pattern) - len(source) mismatches.
        """
        pattern = list(self.pattern)
        source = list(self.pattern)[0:4]
        list_of_shifts = self.P2_exact(self.pattern, source)
        self.assertEqual(list_of_shifts, [])
        pass

P2_SUITE = TestLoader().loadTestsFromTestCase(CBRAHMSTestP2)
