from unittest import TestCase, TestLoader, TestSuite, skip
from nose_parameterized import parameterized, param
from vis.analyzers.indexers import noterest, metre
from tests import tools
from functools import partial # for filling in function settings prior to function call
from LineSegment import TwoDVector, LineSegment
import copy
import cbrahmsGeo
import midiparser
import music21
import pandas
import pdb
import nose


class TestExactMatches(TestCase):
    #TODO a vertical translation-only test. you only have a transposition only test!

    algorithms = {
        "P1_onset" : partial(cbrahmsGeo.P1, option='onset'),
        "P1_segment" : partial(cbrahmsGeo.P1, option='segment'),
        "P2_exact" : partial(cbrahmsGeo.P2, option=0),
        "P2_best" : cbrahmsGeo.P2,
        "P3" : partial(cbrahmsGeo.P3, option=0)
    }

    def setUp(self):
        # Over the Rainbow query
        self.pattern = [LineSegment(d) for d in [[0,4,48],[4,4,60],[8,2,59],[10,1,55],[11,1,57],[12,2,59],[14,2,60]]]
        self.source = copy.deepcopy(self.pattern)

    def tearDown(self):
        pass

    @parameterized.expand(algorithms.items())
    def test_edgecase_source_is_smallerthan_pattern(self, _, algorithm):
        """
        Sources are all possible prefixes of the pattern.
        Expected behaviour depends on the algorithm and length of prefix:

        P1_onset: empty list (as there is no exact match)
        P1_segment: same as P1_onset
        P2_exact: empty list (as there is no exact match)
        P2_best: [(0,0)] (as (0,0) is the match with the highest multiplicity)
            exception: when source length = 1, there are 7 matches since any note will do
        P3: [(0,0)] (as (0,0) results in the longest intersection of line segments)
            exception: when source length = 1, there are 2 matches since there exists a second note ([4,4,60]) with greater than or equal duration to the first note of the pattern, so it can be just as good of an intersection as the first note of the pattern.

        Special cases:
        """
        for i in range(len(self.pattern)):
            list_of_shifts = algorithm(self.pattern, self.source[0:i])
            # P1_onset, P1_segment, and P2_exact should generally return [] since there is no exact match
            if _[:2] == "P1" or _ == "P2_exact":
                self.assertEqual(list_of_shifts, [])
            # Special case 1: When |S|=1, the pattern has a best match with EVERY note
            elif _ == "P2_best" and i == 1:
                self.assertEqual(len(list_of_shifts), 7)
            # Special case 2: In this case, the second note at offset 4 shares the same duration as the source, so it is just as good as (0,0)
            elif _ == "P3" and i == 1:
                self.assertEqual(list_of_shifts, [TwoDVector(0,0), TwoDVector(-4, -12)])
            # P2_best and P3 should generally return (0,0), as that is the best match
            else:
                self.assertEqual(list_of_shifts, [TwoDVector(0,0)])

    @parameterized.expand(algorithms.items())
    def test_edgecase_source_is_transposed_pattern(self, _, algorithm):
        """
        Pattern is a same-size copy of the source, transposed up by an octave.
        """
        # TODO use many transpositions, and horizontal shifts too.
        shift = TwoDVector(0, 12)
        self.source = [p + shift for p in self.pattern]
        list_of_shifts = algorithm(self.pattern, self.source)
        self.assertEqual(list_of_shifts, [shift])

    @parameterized.expand(algorithms.items())
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

    @parameterized.expand(algorithms.items())
    @skip #Desired behaviour?
    def test_edgecase_source_is_two_superimposed_patterns(self, _, algorithm):
        """
        Similar test to above, with the entire pattern duplicated instead of just one note
        """
        self.source.extend(self.source)
        expected_matches = [TwoDVector(0,0), TwoDVector(0,0)]

        list_of_shifts = algorithm(self.pattern, self.source)
        self.assertEqual(list_of_shifts, expected_matches)

    @parameterized.expand(algorithms.items())
    # TODO P2 fails this test, but again is a result of its behaviour. This would make sense, since the translation multiplicity will be double what is expected.
    @skip # Desired behaviour?
    def test_edgecase_pattern_is_duplicated_source_is_pattern(self, _, algorithm):
        """
        Given a source, identical to the pattern, this test tries to find an occurrence of a doubled pattern in the source. For example, if the clarinet and trumpet played in unison, can you find the doubled pattern in the piano reduction, which just has one occurrence of the pattern?
        The expected behaviour should be NO, the algorithm will not find this occurrence, since a doubled pattern should only match exactly with a doubled source.
        """
        self.pattern.extend(self.pattern)
        expected_matches = []
        list_of_shifts = algorithm(self.pattern, self.source)
        self.assertEqual(list_of_shifts, expected_matches)

    @parameterized.expand(algorithms.items())
    def test_source_is_repeated_pattern(self, _, algorithm):
        """
        Creates a source which consists of many pattern repetitions, each being transposed slightly. Then tests whether the algorithm can find each sequential occurrence of the pattern.
        """
        num_repetitions = 300
        expected_matches = [TwoDVector(0, 0)]

        # Repeat the pattern by adding a new occurrence on to the end
        for i in range(1, num_repetitions):
            new_start_onset = self.source[-1].offset + 1
            # Transpose pattern repetitions up to two octaves
            expected_matches.append(TwoDVector(new_start_onset, i % 24))
            self.source.extend([p + expected_matches[i] for p in self.pattern])

        list_of_shifts = algorithm(self.pattern, self.source)
        self.assertEqual(list_of_shifts, expected_matches)

    def test_source_is_fragmented_pattern(self):
        source = [LineSegment(d) for d in ((0,2,48), (2,2,48), (4,2,60), (6,2,60), (8,1,59), (9,1,59), (10,0.5,55), (10.5,0.5,55), (11,0.5,57), (11.5,0.5,57), (12,1,59), (13, 1, 59), (14,1,60), (15,1,60))]
        expected_matches = [TwoDVector(0,0)]
        list_of_shifts = cbrahmsGeo.P3(self.pattern, self.source)
        self.assertEqual(list_of_shifts, expected_matches)


    @parameterized.expand(algorithms.items())
    def test_midiparser_chidori(self, _, algorithm):
        """
        Parses the Chidori Meimei Japanese folk song and searches for all four occurrences of a common four-note motif
        """
        list_of_shifts = tools.run_algorithm_with_midiparser(algorithm, 'music_files/chidori_query.mid', 'music_files/chidori_meimei.mid')
        self.assertEqual(list_of_shifts, [TwoDVector(d[0], d[1]) for d in [[2.0, -10], [6.0, -10], [65.0, -10], [69.0, -10]]])

    @parameterized.expand(algorithms.items())
    def test_midiparser_bwv2(self, _, algorithm):
        """
        Parses Bach's BWV2 chorale and searches for a V-i cadence query
        """
        list_of_shifts = tools.run_algorithm_with_midiparser(algorithm, 'music_files/query_V-i.mid', 'music_files/bach_BWV2_chorale.krn')
        self.assertEqual(list_of_shifts, [TwoDVector(30.0, 0)])


EXACT_MATCHES_SUITE = TestLoader().loadTestsFromTestCase(TestExactMatches)
