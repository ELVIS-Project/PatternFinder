from unittest import TestCase, TestLoader
from vis.analyzers.indexers import noterest, metre
from tests import tools
from functools import partial
from LineSegment import LineSegment, TwoDVector
import cbrahmsGeo
import midiparser
import music21
import pandas
import pdb

import copy

class CBRAHMSTestP2(TestCase):

    def setUp(self):
        # Over the Rainbow query
        self.pattern = [LineSegment(d) for d in [[0,4,48],[4,4,60],[8,2,59],[10,1,55],[11,1,57],[12,2,59],[14,2,60]]]

    def test_edgecase_one_mismatch_same_size(self):
        source = copy.deepcopy(self.pattern)

        self.pattern[0].onset += 1
        list_of_shifts = cbrahmsGeo.P2(self.pattern, source, 1)
        self.assertEqual(list_of_shifts, [TwoDVector(0,0)])

        # Same test with the source transposed
        shift = TwoDVector(0, 5)
        source = [s + shift for s in source]
        list_of_shifts = cbrahmsGeo.P2(self.pattern, source, 1)
        self.assertEqual(list_of_shifts, [TwoDVector(0,5)])

    def test_edgecase_all_no_similarity(self):
        source = [LineSegment([p.onset, p.duration, p.pitch * (p.onset + 100)]) for p in self.pattern] # Assumes no interval is greater than 100 semitones
        list_of_shifts = cbrahmsGeo.P2(self.pattern, source, "all")
        self.assertEqual(len(list_of_shifts), len(self.pattern) * len(source))



P2_SUITE = TestLoader().loadTestsFromTestCase(CBRAHMSTestP2)
