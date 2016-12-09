from unittest import TestCase, TestLoader, TestSuite, skip
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

    P1_onset = partial(cbrahmsGeo.P1, option='onset')
    P1_segment = partial(cbrahmsGeo.P1, option='segment')
    P2 = partial(cbrahmsGeo.P2, option=0)
    P3 = partial(cbrahmsGeo.P3, option=0)
    algorithms=[
        ("P1_onset", P1_onset),
        ("P1_segment", P1_segment),
        ("P2", P2)
        #("P3", P3)
    ]

    def setUp(self):
        # Over the Rainbow query
        self.pattern = [LineSegment(d) for d in [[0,4,48],[4,4,60],[8,2,59],[10,1,55],[11,1,57],[12,2,59],[14,2,60]]]
        self.source = copy.deepcopy(self.pattern)

    def tearDown(self):
        pass

    @parameterized.expand(algorithms)
    def test_edgecase_pattern_larger_than_source(self, _, algorithm):
        """
        Tests P1 with a pattern that is larger than the source. It should return an empty list.
        """
        list_of_shifts = algorithm(self.pattern, self.source[0:4])
        self.assertEqual(list_of_shifts, [])

    @parameterized.expand(algorithms)
    def test_edgecase_identical_source(self, _, algorithm):
        """
        Checks if algorithm can match a pattern with an identical source
        """
        list_of_shifts = algorithm(self.pattern, self.source)
        self.assertEqual(list_of_shifts, [TwoDVector(0,0)])

    @parameterized.expand(algorithms)
    def test_edgecase_source_is_transposed_pattern(self, _, algorithm):
        """
        Checks if algorithm can match a pattern to a source of the same size, but transposed.
        """
        # TODO use many transpositions, and horizontal shifts too.
        shift = TwoDVector(0, 12)
        self.source = [p + shift for p in self.pattern]
        list_of_shifts = algorithm(self.pattern, self.source)
        self.assertEqual(list_of_shifts, [shift])

    @parameterized.expand(algorithms)
    @skip # TODO all algorithms fail this test. What is the desired behaviour? One or two occurrences?
    def test_edgecase_source_has_superimposed_note(self, _, algorithm):
        """
        If the pattern occurs in a source, and within that passage the source has a subset of notes which are duplicated (for example, if the trumpet doubles the clarinet only on the down beats), then the algorithm should find a multiplicity of translations. How many, though? This is instead of the naive behavior, which would find just one occurrence.
        """
        # TODO should duplicate subset of notes (more than one) as well

        for s in self.source:
            # Duplicate a note
            self.source.append(s)
            # Expect two occurrences for a single duplicated note
            expected_matches = [TwoDVector(0,0), TwoDVector(0,0)]
            list_of_shifts = algorithm(self.pattern, self.source)
            self.assertEqual(list_of_shifts, expected_matches)
            # Remove this duplication in preparation for the next iteration
            self.source.remove(s)

    @parameterized.expand(algorithms)
    def test_edgecase_source_is_two_superimposed_patterns(self, _, algorithm):
        """
        Similar test to above, with the entire pattern duplicated instead of just one note
        """
        self.source.extend(self.source)
        expected_matches = [TwoDVector(0,0), TwoDVector(0,0)]

        list_of_shifts = algorithm(self.pattern, self.source)
        self.assertEqual(list_of_shifts, expected_matches)

    @parameterized.expand(algorithms)
    # TODO P2 fails this test, but again is a result of its behaviour. This would make sense, since the translation multiplicity will be double what is expected.
    def test_edgecase_pattern_is_duplicated_source_is_pattern(self, _, algorithm):
        """
        Given a source, identical to the pattern, this test tries to find an occurrence of a doubled pattern in the source. For example, if the clarinet and trumpet played in unison, can you find their combined part within the piano part, which also plays in unison?
        The expected behaviour should be NO, the algorithm will not find this occurrence, since a doubled pattern should only match exactly with a doubled source.
        """
        self.pattern.extend(self.pattern)
        expected_matches = []
        list_of_shifts = algorithm(self.pattern, self.source)
        self.assertEqual(list_of_shifts, expected_matches)

    @parameterized.expand(algorithms)
    def test_source_is_repeated_pattern(self, _, algorithm):
        """
        Creates a source which consists of many pattern repetitions, each being transposed slightly
        Tests whether algorithm can find each sequential occurrence of the pattern.
        """
        num_repetitions = 300
        expected_matches = [TwoDVector(0, 0)]

        # Repeat the pattern by adding a new occurrence on to the end
        for i in range(1, num_repetitions):
            new_start_onset = self.source[-1].onset + 1
            # Transpose pattern repetitions up to two octaves
            expected_matches.append(TwoDVector(new_start_onset, i % 24))
            self.source.extend([p + expected_matches[i] for p in self.pattern])

        list_of_shifts = algorithm(self.pattern, self.source)
        self.assertEqual(list_of_shifts, expected_matches)

    @parameterized.expand(algorithms)
    def test_midiparser_chidori(self, _, algorithm):
        """
        Parses the Chidori Meimei Japanese folk song and searches for all four occurrences of a common four-note motif
        """
        list_of_shifts = tools.run_algorithm_with_midiparser(algorithm, 'music_files/chidori_query.mid', 'music_files/chidori_meimei.mid')
        self.assertEqual(list_of_shifts, [TwoDVector(d[0], d[1]) for d in [[2.0, -10], [6.0, -10], [65.0, -10], [69.0, -10]]])

    @parameterized.expand(algorithms)
    def test_midiparser_bwv2(self, _, algorithm):
        """
        Parses Bach's BWV2 chorale and searches for a V-i cadence query
        """
        list_of_shifts = tools.run_algorithm_with_midiparser(algorithm, 'music_files/query_V-i.mid', 'music_files/bach_BWV2_chorale.krn')
        self.assertEqual(list_of_shifts, [TwoDVector(30.0, 0)])


EXACT_MATCHES_SUITE = TestLoader().loadTestsFromTestCase(CBRAHMSTestExactMatches)
