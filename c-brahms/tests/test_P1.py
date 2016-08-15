from unittest import TestCase, TestLoader
from vis.analyzers.indexers import noterest, metre
from tests import tools
import cbrahmsGeo
import midiparser
import music21
import pandas
import pdb


class CBRAHMSTestP1(TestCase):

    def setUp(self):
        # Over the Rainbow query
        self.pattern = [[0,48],[4,60],[8,59],[10,55],[11,57],[12,59],[14,60]]

    def tearDown(self):
        pass

    def test_P1_edgecase_same_size_transposed(self):
        """
        Checks if P1 can match a pattern to a source of the same size, but transposed.
        """
        # transpose pattern 12 semitones upwards
        shift = [0,12]
        source = tools.shift_pattern(shift, self.pattern)
        list_of_shifts = cbrahmsGeo.P1(self.pattern, source)
        self.assertEqual(list_of_shifts, [shift])

    def test_P1_edgecase_identical_source(self):
        """
        Checks if P1 can match a pattern with an identical source
        """
        source = list(self.pattern)
        list_of_shifts = cbrahmsGeo.P1(self.pattern, source)
        self.assertEqual(list_of_shifts, [[0,0]])

    def test_P1_repeated_pattern_in_source(self):
        """
        Translates a pattern automatically, and checks to see if P1 can find all of the translations
        """
        source = list(self.pattern)
        num_repetitions = 1000
        expected_matches = [[0,0]]

        # Repeat the pattern by adding a new occurrence on to the end
        for i in range(1, num_repetitions):
            new_start_onset = source[-1][0] + 1
            # Transpose pattern repetitions up to two octaves
            expected_matches.append([new_start_onset, i % 24])
            source.extend(tools.shift_pattern(expected_matches[i], self.pattern))

        list_of_shifts = cbrahmsGeo.P1(self.pattern, source)
        self.assertEqual(list_of_shifts, expected_matches)

    def test_P1_edgecase_pattern_larger_than_source(self):
        """
        Tests P1 with a pattern that is larger than the source. It should return an empty list.
        """
        pattern = list(self.pattern)
        source = list(self.pattern)[0:4]
        list_of_shifts = cbrahmsGeo.P1(self.pattern, source)
        self.assertEqual(list_of_shifts, [])

    def test_P1_midiparser_chidori(self):
        """
        Parses the Chidori Meimei Japanese folk song and searches for all four occurrences of a common four-note motif
        """
        list_of_shifts = tools.run_algorithm_with_midiparser(cbrahmsGeo.P1, 'music_files/chidori_query.mid', 'music_files/chidori_meimei.mid')
        self.assertEqual(list_of_shifts, [[2.0, -10], [6.0, -10], [65.0, -10], [69.0, -10]])


    def test_P1_midiparser_bwv2(self):
        list_of_shifts = tools.run_algorithm_with_midiparser(cbrahmsGeo.P1, 'music_files/query_V-i.mid', 'music_files/bach_BWV2_chorale.krn')
        self.assertEqual(list_of_shifts, [[30.0, 0]])

P1_SUITE = TestLoader().loadTestsFromTestCase(CBRAHMSTestP1)
