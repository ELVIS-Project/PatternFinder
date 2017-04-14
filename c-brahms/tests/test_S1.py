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
        #todo why does this break with needing 3 arguments???! i don't need the duration here??
        self.pattern = [LineSegment(*s) for s in [(0,48,4),(4,60,4),(8,59,2),(10,55,1),(11,57,1),(12,59,2),(14,60,2)]]
        self.lemstrom_score = "music_files/lemstrom2011_test/leiermann.xml"
        self.lemstrom_pattern = "music_files/lemstrom2011_test/query_c.mid"

    def tearDown(self):
        pass


    def test_intra_vectors_lemstrom(self):
        """
        Checks whether the LineSegmentSet Class can correctly identify the intra-database vectors as given in Lemstrom's paper
        """
        # The paper writes a collection of intra-database vectors that are supposed to be generated from ignoring the first measure and setting a window size of 3
        source = LineSegmentSet(tools.parse_source_from_score(self.lemstrom_score))
        # Get intra-database vectors: ignore first measure, set w=3
        source.compute_intra_vectors(window = 3, start = 10)
        lemstrom_vectors = [TwoDVector(float(v[0]) / 4, v[1]) for v in [
                (0,7), (0,12), (0,5), (2,8), #(2,15), (4,4),
                (2,3), (4,-1), (4,2), (2,-4), (2,-1), (4,-8),
                (0,3), (2,-4), (4,3), (2,-7), (8,-14), #(4,0) # edited (6,-14) -> (8,-14)
                (2,7), (4,-7), (4,0), (2,-14), (2,-7), (2,-2),
                (0,7), (0,12), (0,24), (0,5), (0,17), (1,24),
                (0,12), (1,19), (2,17), (1,7), (2,5), (3,8),
                (1,-2), (2,1), (3,0), (1,3), (2,2), (4,-14),
                (1,-1), (3,-17), (3,-8), (2,-16), (4,-17), #(2,-7), # edited (4,-18) -> (4,-17)
                (0,9), (2,-1), (2,11), (2,-10), (2,2), (4,-12),
                (0,12), (2,13), (0,0), (0,15), #(2,-14), (2,-2), # edited (0,1) -> (0,0)
                (0,5), (0,12), (2,1), (2,3), (4,-14), (4,-2), (4,-1), (6,-7), (6,0)]] #These we add because Lemstrom's data seems to be incomplete in accordance to the musical excerpt
        intended = sorted(source.ivs)
        actual = sorted(lemstrom_vectors)
        self.longMessage = True
        self.assertListEqual(intended, actual, msg = "\nINTENDED\n" + pformat(list(enumerate(sorted(source.ivs_indices)))) + "\nACTUAL\n" + pformat(list(enumerate(sorted(actual)))))

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

    def test_Ktable_lemstrom(self):
        source = LineSegmentSet(tools.parse_source_from_score(self.lemstrom_score))
        pattern = LineSegmentSet(tools.parse_pattern_from_score(self.lemstrom_pattern))

        #source.compute_intra_vectors(window = 3, start = 10)
        pattern.initialize_Ktables(source, 3)

    def test_lemstrom(self):
        algorithm = partial(S1, window = 3)
        result = tools.run_algorithm_with_midiparser(algorithm, self.lemstrom_pattern, self.lemstrom_score)
        self.assertEqual([TwoDVector(3,-10)], result)

S1_SUITE = TestLoader().loadTestsFromTestCase(TestS1)

if __name__ == '__main__':
    #TextTestRunner(verbosity=2).run(S1_SUITE)
    S1_SUITE.debug()
