from unittest import TestCase, TestLoader, TestSuite
from nose_parameterized import parameterized
from vis.analyzers.indexers import noterest, metre
from tests import tools
from functools import partial
from LineSegment import TwoDVector, LineSegment
import copy
import cbrahmsGeo
import midiparser
import music21
import pandas
import pdb
import nose


class CBRAHMSTestExactMatches(TestCase):

    P1 = partial(cbrahmsGeo.P1, option='onset')
    P2 = partial(cbrahmsGeo.P2, option=0)
    P3 = partial(cbrahmsGeo.P3, option=0)
    algorithms=[
        ("P1", P1),
        ("P2", P2),
        ("P3", P3)
    ]

    def setUp(self):
        # Over the Rainbow query
        self.pattern = [LineSegment(d) for d in [[0,4,48],[4,4,60],[8,2,59],[10,1,55],[11,1,57],[12,2,59],[14,2,60]]]
        self.source = copy.deepcopy(self.pattern)
        self.P1 = cbrahmsGeo.P1
        self.P2 = cbrahmsGeo.P2
        self.P3 = cbrahmsGeo.P3

    def tearDown(self):
        pass

    """
    Tests P1 with a pattern that is larger than the source. It should return an empty list.
    """
    @parameterized.expand(algorithms)
    def test_edgecase_pattern_larger_than_source(self, _, algorithm):
        list_of_shifts = algorithm(self.pattern, self.source[0:4])
        self.assertEqual(list_of_shifts, [])

    """
    IDENTIAL SOURCE:
    Checks if algorithm can match a pattern with an identical source
    """
    @parameterized.expand(algorithms)
    def test_edgecase_identical_source(self, _, algorithm):
        list_of_shifts = algorithm(self.pattern, self.source)
        self.assertEqual(list_of_shifts, [TwoDVector(0,0)])

    """
    SAME SIZE TRANSPOSED:
    Checks if algorithm can match a pattern to a source of the same size, but transposed.
    """
    @parameterized.expand(algorithms)
    def test_edgecase_same_size_transposed(self, _, algorithm):
        shift = TwoDVector(0, 12)
        self.source = [p + shift for p in self.pattern]
        list_of_shifts = algorithm(self.pattern, self.source)
        self.assertEqual(list_of_shifts, [shift])

    """
    Translates a pattern automatically to confirm algorithm can find all of the translations
    """
    @parameterized.expand(algorithms)
    def test_repeated_pattern_in_source(self, _, algorithm):
        num_repetitions = 1000
        expected_matches = [TwoDVector(0, 0)]

        # Repeat the pattern by adding a new occurrence on to the end
        for i in range(1, num_repetitions):
            new_start_onset = self.source[-1].onset + 1
            # Transpose pattern repetitions up to two octaves
            expected_matches.append(TwoDVector(new_start_onset, i % 24))
            self.source.extend([p + expected_matches[i] for p in self.pattern])

        list_of_shifts = algorithm(self.pattern, self.source)
        self.assertEqual(list_of_shifts, expected_matches)

    """
    CHIDORI MEIMEI:
    Parses the Chidori Meimei Japanese folk song and searches for all four occurrences of a common four-note motif
    """
    @parameterized.expand(algorithms)
    def test_midiparser_chidori(self, _, algorithm):
        list_of_shifts = tools.run_algorithm_with_midiparser(algorithm, 'music_files/chidori_query.mid', 'music_files/chidori_meimei.mid')
        self.assertEqual(list_of_shifts, [TwoDVector(d[0], d[1]) for d in [[2.0, -10], [6.0, -10], [65.0, -10], [69.0, -10]]])

    """
    BWV2:
    Parses Bach's BWV2 chorale and searches for a V-i cadence query
    """
    @parameterized.expand(algorithms)
    def test_midiparser_bwv2(self, _, algorithm):
        list_of_shifts = tools.run_algorithm_with_midiparser(algorithm, 'music_files/query_V-i.mid', 'music_files/bach_BWV2_chorale.krn')
        self.assertEqual(list_of_shifts, [TwoDVector(30.0, 0)])

EXACT_MATCHES_SUITE = TestLoader().loadTestsFromTestCase(CBRAHMSTestExactMatches)
