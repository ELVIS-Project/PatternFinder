from unittest import TestCase, TestLoader, expectedFailure
from nose_parameterized import parameterized
from functools import partial
import random
from vis.analyzers.indexers import noterest, metre
from tests import tools
from LineSegment import LineSegment, TwoDVector
import cbrahmsGeo
import midiparser
import music21
import pandas
import copy
import pdb

def n_segment_tests(n, pattern, source):

    mod_pattern = copy.deepcopy(pattern)
    mod_source = copy.deepcopy(source)
    expected_result = TwoDVector(0,0)
    test_name = ""

    def exact(): # default behaviour
        pass
    def translation(gap): # gap = 0 for sequential
        mod_source = [s + TwoDVector(source[-1].offset + gap, 0) for s in source]
    def onset_synch():
        pass
    def offset_synch():
        pass

    def transposition(t):
        test_name += ("transposed_by_" + t)
        mod_source = [s + TwoDVector(0, t) for s in source]
        mod_expected_result = expected_result + TwoDVector(0, t)

    def pattern_duration_multiply(factor):
        mod_pattern = [p * factor for p in pattern]

    for pitch_mod in [transposition(0), transposition(4)]:
        yield (test_name, mod_pattern, mod_source, mod_expected_result)

class TestP3(TestCase):

    PATTERN = [LineSegment(d) for d in ((0,4,48),(4,4,60),(8,2,59),(10,1,55),(11,1,57),(12,2,59),(14,2,60))]
    SOURCE = copy.deepcopy(PATTERN)

    one_segment_tests_auto = list(n_segment_tests(1, PATTERN, SOURCE))

    # TODO auto-generate all sorts of modifications for source & pattern
    one_segment_tests = [
            # ("Test Name", ((pattern), (source), (expected_shift)))
            ("same_size_superimposed", ((0, 4, 60), (0, 4, 60), (0,0))),
            ("same_size_sequential", ((0, 4, 60), (4, 4, 60), (4,0))),
            ("same_size_sequential_transposed", ((0,4,60), (4,4,64), (4,4))),
            ("same_size_with_gap", ((0,4,60), (6,4,60), (6,0))),
            ("same_size_with_gap_transposed", ((0,4,60), (6,4,64), (6,4)))]
            # onsetsynch & offsetsynch: not sure of the desired behaviour. when |P| < |S| and P \in S, there are technically an uncountably infinite number of valid shifts. Currently, onsetsynch finds (0,0) and (2,0) (it only finds the shifts which have corresponding turning points)
            #("pattern_smallerthan_source_onsetsynch", ((0,2,60), (0,4,60), (0,0))),
            #("pattern_smallerthan_source_onsetsynch_transposed", ((0,2,60), (0,4,64), (0,4)))
            #("pattern_smallerthan_source_offsetsynch", ((0,2,60), (0,4,60))),
            #("pattern_smallerthan_source_offsetsynch_transposed", ((0,2,60), (0,4,64))),

    def setUp(self):
        # Over the Rainbow query
        self.pattern = [LineSegment(d) for d in [[0,4,60], [4,4,64]]]
        # Identical source
        self.source = copy.deepcopy(self.pattern)

    @parameterized.expand(one_segment_tests_auto)
    def test_one_segment(self, _, test):
        """
        Tests P3 with a pattern that is larger than the source. It should return an empty list.
        """
        pattern = [LineSegment(test[0])]
        source = [LineSegment(test[1])]
        expected_result = [TwoDVector(test[2][0], test[2][1])]
        list_of_shifts = cbrahmsGeo.P3(pattern, source)
        self.assertEqual(list_of_shifts, expected_result)

    def test_source_is_transposed_and_translated_pattern(self):
        for s in self.source:
            s.x += 4
            s.onset += 4
            s.offset += 2
            s.duration = 2
        list_of_shifts = cbrahmsGeo.P3(self.pattern, self.source)
        self.assertEqual([TwoDVector(4, 0)], list_of_shifts)

    def test_source_is_fragmented_pattern(self):
        source = [LineSegment(d) for d in ((0,4,48),(4,4,60),(8,2,59),(10,1,55),(11,1,57),(12,2,59),(14,2,60))]



P3_SUITE = TestLoader().loadTestsFromTestCase(TestP3)
