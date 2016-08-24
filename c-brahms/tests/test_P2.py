from unittest import TestCase, TestLoader
from vis.analyzers.indexers import noterest, metre
from tests import tools
from functools import partial
import cbrahmsGeo
import midiparser
import music21
import pandas
import pdb

import copy

class CBRAHMSTestP2(TestCase):

    def setUp(self):
        # Over the Rainbow query
        self.pattern = [[0,48],[4,60],[8,59],[10,55],[11,57],[12,59],[14,60]]

    def test_edgecase_one_mismatch_same_size(self):
        source = copy.deepcopy(self.pattern[:])

        self.pattern[0][1] += 1 #fails because this modifies the source list?!
        list_of_shifts = cbrahmsGeo.P2(self.pattern, source, 1)
        self.assertEqual(list_of_shifts, [[0,0]])

        # Same test with the pattern transposed
        source = tools.shift_pattern([0,5], source)
        list_of_shifts = cbrahmsGeo.P2(self.pattern, source, 1)
        self.assertEqual(list_of_shifts, [[0,5]])

    def test_edgecase_all_no_similarity(self):
        source = [[i, j * (i + 100)] for i,j in self.pattern] # Assumes no interval is greater than 100 semitones
        list_of_shifts = cbrahmsGeo.P2(self.pattern, source, "all")
        self.assertEqual(len(list_of_shifts), len(self.pattern) * len(source))



P2_SUITE = TestLoader().loadTestsFromTestCase(CBRAHMSTestP2)
