from unittest import TestCase, TestLoader, TextTestRunner
from vis.analyzers.indexers import noterest, metre
from tests import tools
from collections import Counter # To check for equality between intra-database vector sets
from LineSegment import LineSegmentSet, TwoDVector, LineSegment
from pprint import pformat # for assert error messages to pprint data objects
from cbrahmsGeo import S1
from functools import partial # to set S1 options before passing it to midiparser
import midiparser
import music21
import pandas
import pdb


class TestS1(TestCase):

    def setUp(self):
        # Over the Rainbow query
        #TODO why does this break with needing 3 arguments???! i don't need the duration here??
        self.pattern = [LineSegment(*s) for s in [(0,48,4),(4,60,4),(8,59,2),(10,55,1),(11,57,1),(12,59,2),(14,60,2)]]
        self.lemstrom_score = "music_files/lemstrom2011_test/leiermann.xml"
        self.lemstrom_pattern = "music_files/lemstrom2011_test/query_c.mid"

    def tearDown(self):
        pass


        ### Very odd: in python console, {TwoDVector(4,12) : 1} == {TwoDVector(4,12) : 1} evaluates to false, so the counters do not compare properly. Something must be weird with the equality of TwoDVector objects in Counter(), also since the Counter tallies don't work and instead make a new hash key for each entry in a list of segments.

    def test_intra_vectors_rainbow(self):
        source = LineSegmentSet(self.pattern)
        source.compute_intra_vectors(window = len(source))
        rainbow_vectors = [
                (4,12), (8,11), (10,7), (11,9), (12,11), (14,12),
                (4,-1), (6,-5), (7,-3), (8,-1), (10,0),
                (2,-4), (3,-2), (4,0), (6,1),
                (1,2), (2,4), (4,5),
                (1,2), (3,3),
                (2,1)]
        intended = sorted(source.ivs)
        actual = sorted(TwoDVector(*x) for x in rainbow_vectors)
        self.assertEqual(intended, actual, msg = "\nINTENDED\n" + pformat(intended) + "\nACTUAL\n" + pformat(actual))


S1_SUITE = TestLoader().loadTestsFromTestCase(TestS1)

if __name__ == '__main__':
    TextTestRunner(verbosity=2).run(S1_SUITE)
