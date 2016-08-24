from unittest import TestCase, TestLoader, TestSuite
from vis.analyzers.indexers import noterest, metre
from tests import tools
from functools import partial
import cbrahmsGeo
import midiparser
import music21
import pandas
import pdb
import nose


class CBRAHMSTestExactMatches(TestCase):

    def setUp(self):
        # Over the Rainbow query
        self.pattern = [[0,48],[4,60],[8,59],[10,55],[11,57],[12,59],[14,60]]
        self.P1 = cbrahmsGeo.P1
        self.P2 = cbrahmsGeo.P2
        self.P3 = cbrahmsGeo.P3

    def tearDown(self):
        pass

    """
    Tests P1 with a pattern that is larger than the source. It should return an empty list.
    """
    def test_P1_edgecase_pattern_larger_than_source(self):
        pattern = list(self.pattern)
        source = list(self.pattern)[0:4]
        list_of_shifts = cbrahmsGeo.P1(self.pattern, source, 'onset')
        self.assertEqual(list_of_shifts, [])
    def test_P2_edgecase_pattern_larger_than_source(self):
        pattern = list(self.pattern)
        source = list(self.pattern)[0:4]
        list_of_shifts = self.P2(self.pattern, source, 0)
        self.assertEqual(list_of_shifts, [])
    def test_P3_edgecase_pattern_larger_than_source(self):
        pattern = list(self.pattern)
        source = list(self.pattern)[0:4]
        list_of_shifts = self.P3(self.pattern, source, 0)
        self.assertEqual(list_of_shifts, [])

    """
    IDENTIAL SOURCE:
    Checks if algorithm can match a pattern with an identical source
    """
    def test_P1_edgecase_identical_source(self):
        source = list(self.pattern)
        list_of_shifts = self.P1(self.pattern, source, 'onset')
        self.assertEqual(list_of_shifts, [[0,0]])
    def test_P2_edgecase_identical_source(self):
        source = list(self.pattern)
        list_of_shifts = self.P2(self.pattern, source, 0)
        self.assertEqual(list_of_shifts, [[0,0]])
    def test_P3_edgecase_identical_source(self):
        source = list(self.pattern)
        list_of_shifts = self.P2(self.pattern, source, 0)
        self.assertEqual(list_of_shifts, [[0,0]])

    """
    SAME SIZE TRANSPOSED:
    Checks if algorithm can match a pattern to a source of the same size, but transposed.
    """
    def test_P1_edgecase_same_size_transposed(self):
        shift = [0,12]
        source = tools.shift_pattern(shift, self.pattern)
        list_of_shifts = self.P1(self.pattern, source, 'onset')
        self.assertEqual(list_of_shifts, [shift])
    def test_P2_edgecase_same_size_transposed(self):
        shift = [0,12]
        source = tools.shift_pattern(shift, self.pattern)
        list_of_shifts = self.P2(self.pattern, source, 0)
        self.assertEqual(list_of_shifts, [shift])
    def test_P3_edgecase_same_size_transposed(self):
        shift = [0,12]
        source = tools.shift_pattern(shift, self.pattern)
        list_of_shifts = self.P3(self.pattern, source, 0)
        self.assertEqual(list_of_shifts, [shift])

    """
    Translates a pattern automatically to confirm algorithm can find all of the translations
    """
    def test_P1_repeated_pattern_in_source(self):
        source = list(self.pattern)
        num_repetitions = 1000
        expected_matches = [[0,0]]

        # Repeat the pattern by adding a new occurrence on to the end
        for i in range(1, num_repetitions):
            new_start_onset = source[-1][0] + 1
            # Transpose pattern repetitions up to two octaves
            expected_matches.append([new_start_onset, i % 24])
            source.extend(tools.shift_pattern(expected_matches[i], self.pattern))

        list_of_shifts = self.P1(self.pattern, source, 'onset')
        self.assertEqual(list_of_shifts, expected_matches)
    def test_P2_repeated_pattern_in_source(self):
        source = list(self.pattern)
        num_repetitions = 1000
        expected_matches = [[0,0]]

        # Repeat the pattern by adding a new occurrence on to the end
        for i in range(1, num_repetitions):
            new_start_onset = source[-1][0] + 1
            # Transpose pattern repetitions up to two octaves
            expected_matches.append([new_start_onset, i % 24])
            source.extend(tools.shift_pattern(expected_matches[i], self.pattern))

        list_of_shifts = self.P2(self.pattern, source, 0)
        self.assertEqual(list_of_shifts, expected_matches)
    def test_P3_repeated_pattern_in_source(self):
        source = list(self.pattern)
        num_repetitions = 1000
        expected_matches = [[0,0]]

        # Repeat the pattern by adding a new occurrence on to the end
        for i in range(1, num_repetitions):
            new_start_onset = source[-1][0] + 1
            # Transpose pattern repetitions up to two octaves
            expected_matches.append([new_start_onset, i % 24])
            source.extend(tools.shift_pattern(expected_matches[i], self.pattern))

        list_of_shifts = self.P3(self.pattern, source, 0)
        self.assertEqual(list_of_shifts, expected_matches)

    """
    CHIDORI MEIMEI:
    Parses the Chidori Meimei Japanese folk song and searches for all four occurrences of a common four-note motif
    """
    def test_P1_midiparser_chidori(self):
        list_of_shifts = tools.run_algorithm_with_midiparser(self.P1, 'music_files/chidori_query.mid', 'music_files/chidori_meimei.mid', 'onset')
        self.assertEqual(list_of_shifts, [[2.0, -10], [6.0, -10], [65.0, -10], [69.0, -10]])
    def test_P2_midiparser_chidori(self):
        list_of_shifts = tools.run_algorithm_with_midiparser(self.P2, 'music_files/chidori_query.mid', 'music_files/chidori_meimei.mid', 0)
        self.assertEqual(list_of_shifts, [[2.0, -10], [6.0, -10], [65.0, -10], [69.0, -10]])
    def test_P3_midiparser_chidori(self):
        list_of_shifts = tools.run_algorithm_with_midiparser(self.P3, 'music_files/chidori_query.mid', 'music_files/chidori_meimei.mid', 0)
        self.assertEqual(list_of_shifts, [[2.0, -10], [6.0, -10], [65.0, -10], [69.0, -10]])

    """
    BWV2:
    Parses Bach's BWV2 chorale and searches for a V-i cadence query
    """
    def test_P1_midiparser_bwv2(self):
        list_of_shifts = tools.run_algorithm_with_midiparser(self.P1, 'music_files/query_V-i.mid', 'music_files/bach_BWV2_chorale.krn', 'onset')
        self.assertEqual(list_of_shifts, [[30.0, 0]])
    def test_P2_midiparser_bwv2(self):
        list_of_shifts = tools.run_algorithm_with_midiparser(self.P2, 'music_files/query_V-i.mid', 'music_files/bach_BWV2_chorale.krn', 0)
        self.assertEqual(list_of_shifts, [[30.0, 0]])
    def test_P3_midiparser_bwv2(self):
        list_of_shifts = tools.run_algorithm_with_midiparser(self.P3, 'music_files/query_V-i.mid', 'music_files/bach_BWV2_chorale.krn', 0)
        self.assertEqual(list_of_shifts, [[30.0, 0]])


EXACT_MATCHES_SUITE = TestLoader().loadTestsFromTestCase(CBRAHMSTestExactMatches)
