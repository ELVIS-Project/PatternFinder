from unittest import TestCase, TestLoader, TextTestRunner
from tests import tools
from functools import partial
from nose_parameterized import parameterized, param
from LineSegment import TwoDVector, LineSegmentSet
from pprint import pformat # for pretty printing test error messages
from geometric_algorithms import S1, S2, W1, W2
from fractions import Fraction # for scale settings
import music21
import NoteSegment
import cbrahmsGeo
import midiparser
import pdb


lemstrom_pattern = lambda x: 'music_files/lemstrom2011_test/query_' + x + '.mid'
lemstrom_score = 'music_files/lemstrom2011_test/leiermann.xml'

algorithm_W = [("W1", W1), ("W2", W2)]
algorithm_S = [("S1", S1), ("S2", S2)] + algorithm_W
algorithm_P = algorithm_S + algorithm_W

class TestLemstromExample(TestCase):

    # List of queries. To add new tests - format is ("query_filename", [list of algorithms tuples e.g. ("algy-name", function) to test this query], [expected results])
    QUERIES = [
            ('a', (S1, S2, W1, W2), (3.0, -10), {'scale' : 1, 'threshold' : 5}),
            #('b', (S2, W2), (3.0, -10), {'scale' : 1, 'threshold' : 'max'),
            ('c', (S1, S2, W1, W2), (3.0, -10), {'scale' : Fraction(1, 3), 'threshold' : 5}),
            #('d', (S2, W2), (3.0, -10), {'scale' : Fraction(1,3), 'threshold' : 'max'}),
            ('e', (W1, W2), (3.0, -10), {'threshold' : 5})
            #('f', (W2,), (3.0, -10))
    ]

    TESTS = reduce(lambda x, y: x+y, [[{ #concatenate the lists
            'query' : q,
            'algorithm' : algy,
            'expected' : e
        } for algy in a] for (q, a, e, s) in QUERIES])

    def custom_func_name(testcase_func, param_num, param):
        return "%s_algorithm_%s_Query_%s" % (
                testcase_func.__name__,
                param[1]['algorithm'].__name__, #algorithm[0] for string name
                param[1]['query']
        )

    @parameterized.expand([param(**case) for case in TESTS], testcase_func_name = custom_func_name)
    def test(self, query, algorithm, expected, settings={}):
        carlos = algorithm(lemstrom_pattern(query), lemstrom_score, settings)
        carlos.run()
        self.assertEqual(len(carlos.occurrences), 1)
        self.assertEqual(carlos.occurrences[0].shift, (3.0, -10))

    def test_intra_vectors_NOTESEGMENT(self):
        """
        Checks if the NoteSegments class can do the intra-vector work
        """
        source = NoteSegment.NoteSegments(music21.converter.parse(lemstrom_score))
        pattern = NoteSegment.NoteSegments(music21.converter.parse(lemstrom_pattern('c')))

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
        source = LineSegmentSet(tools.parse_source_from_score(lemstrom_score))
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
