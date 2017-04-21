from unittest import TestCase, TestLoader, TextTestRunner
from tests import tools
from functools import partial
from nose_parameterized import parameterized
from LineSegment import TwoDVector, LineSegmentSet
from pprint import pformat # for pretty printing test error messages
from geometric_algorithms.S1 import S1
from geometric_algorithms.S2 import S2
from fractions import Fraction # for scale settings
import music21
import NoteSegment
import cbrahmsGeo
import midiparser
import pdb


class TestLemstromExample(TestCase):

    def setUp(self):
        self.lemstrom_score = 'music_files/lemstrom2011_test/leiermann.xml'
        # A function to return a query file name. Usage: self.lemstrom_pattern('a') --> 'query_a.mid'
        self.lemstrom_pattern = lambda x: 'music_files/lemstrom2011_test/query_' + x + '.mid'

    def tearDown(self):
        pass

    @parameterized.expand([
        ("S1", S1),
        ("S2", S2)
    ])
    def test_lemstrom_QUERY_A_music21(self, _, algorithm):
        """
        Exact match QUERY A ||| P1-3, S1-2, W1-2 Using Music21 and the NoteSegment class
        Parses the ground truth polyphonic music example provided in Lemstrom and Laitninen's 2011 paper. Query A should be found by all algorithms if their error tolerance is zero.
        """
        settings = {'scale' : 1, 'threshold' : 5}
        carlos = algorithm(self.lemstrom_pattern('a'), self.lemstrom_score, settings)
        carlos.run()
        self.assertEqual(len(carlos.occurrences), 1)
        self.assertEqual(carlos.occurrences[0].shift, (3.0, -10))

    @parameterized.expand([
        ("S1", S1),
        ("S2", S2)
    ])
    def test_lemstrom_QUERY_C_music21(self, _, algorithm):
        """
        Exact scaled match QUERY C ||| S1-2, W1-2
        Query C is an exact match scaled by a factor of 3
        """
        settings = {'scale' : Fraction(1,3), 'threshold' : 5}
        carlos = algorithm(self.lemstrom_pattern('c'), self.lemstrom_score, settings)
        carlos.run()
        self.assertEqual(len(carlos.occurrences), 1)
        self.assertEqual(carlos.occurrences[0].shift, (3.0, -10))

    @parameterized.expand([
        #("P1_onset", partial(cbrahmsGeo.P1, option = 'onset')),
        #("P1_segment", partial(cbrahmsGeo.P1, option = 'segment')),
        #("P2", partial(cbrahmsGeo.P2, option = 0)),
        #("P3", partial(cbrahmsGeo.P3, option = 0)),
        #("S1", S1),
        #("S2", partial(S2, threshold = 5))

    ])
    def test_EXACT_midiparser_lemstrom_example(self, _, algorithm):
        """
        Exact match QUERY A ||| P1-3, S1-2, W1-2
        Parses the ground truth polyphonic music example provided in Lemstrom and Laitninen's 2011 paper. Query A should be found by all algorithms if their error tolerance is zero.
        """
        list_of_shifts = tools.run_algorithm_with_midiparser(algorithm, self.lemstrom_pattern('a'), self.lemstrom_score)
        self.assertEqual(list_of_shifts, [TwoDVector(3.0, -10)])

    @parameterized.expand([
        #("P2", partial(cbrahmsGeo.P2, option = 1)),
        #("S2", partial(S2, threshold = 4)) # recall S family algorithms count "matching pairs". Since there are 6 notes in the pattern, and counting 1 mismatch, that makes 4 intra-pattern vector "matching pairs" required
    ])
    def test_PARTIAL_midiparser_lemstrom_example(self, _, algorithm):
        """
        One mismatch QUERY B ||| P2, S2, W2
        Parses the ground truth polyphonic music example provided in Lemstrom and Laitninen's 2011 paper. It should be able to find query B with option = 1 mismatch.
        """
        one_mismatch = tools.run_algorithm_with_midiparser(algorithm, self.lemstrom_pattern('b'), self.lemstrom_score)
        self.assertEqual(one_mismatch, [TwoDVector(3.0, -10)])

    @parameterized.expand([
        #("S1", partial(S1, window = 3, start = 10)),
        #("S2", partial(S2, threshold = 5))
    ])
    def test_SCALED_midiparser_lemstrom_example(self, _, algorithm):
        """
        Exact scaled match QUERY C ||| S1-2, W1-2
        Query C is an exact match scaled by a factor of 3
        """
        result = tools.run_algorithm_with_midiparser(algorithm, self.lemstrom_pattern('c'), self.lemstrom_score)
        self.assertEqual([TwoDVector(3,-10)], result)

    def test_intra_vectors_NOTESEGMENT(self):
        """
        Checks if the NoteSegments class can do the intra-vector work
        """
        source = NoteSegment.NoteSegments(music21.converter.parse(self.lemstrom_score))
        pattern = NoteSegment.NoteSegments(music21.converter.parse(self.lemstrom_pattern('c')))

        # Sort
        source.lexicographic_sort()
        pattern.lexicographic_sort()

        # Get vectors
        pattern.compute_intra_vectors(window = 3)
        source.compute_intra_vectors(window = 3)

        # Ignore first measure
        source.ivs = [v for v in source.ivs if source.flat.notes.index(v.start) >= 10]

        # Lemstrom's Vectors from his paper
        lemstrom_vectors = [(float(v[0]) / 4, v[1]) for v in [
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

        # Sort the lists of vectors lexicographically
        result = sorted([(v.x, v.y) for v in source.ivs])
        actual = sorted(lemstrom_vectors)

        # Assert and give an error message if false
        self.longMessage = True
        self.assertListEqual(result, actual, msg = "\nRESULT\n" + pformat(list(enumerate(sorted(source.ivs)))) + "\nACTUAL\n" + pformat(list(enumerate(sorted(actual)))))

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

    def test_Ktable_lemstrom(self):
        pass
        #source = LineSegmentSet(tools.parse_source_from_score(self.lemstrom_score))
        #pattern = LineSegmentSet(tools.parse_pattern_from_score(self.lemstrom_pattern))

        #source.compute_intra_vectors(window = 3, start = 10)
        #pattern.initialize_Ktables(source, 3)


LEMSTROM_EXAMPLE_SUITE = TestLoader().loadTestsFromTestCase(TestLemstromExample)

if __name__ == "__main__":
    #result = TextTestRunner(verbosity=2).run(LEMSTROM_EXAMPLE_SUITE)
    LEMSTROM_EXAMPLE_SUITE.debug()
