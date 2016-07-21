import cbrahmsGeo
import midiparser
from unittest import TestCase, TestLoader
import pdb

def shift_pattern(shift, pattern):
    """
    Used internally by class CBRAHMSTest
    Input:
        shift: 2-d vector (two-element list)
        pattern: 2-d vectors (list of two-element lists) 
    Output: a new list of the vectors in 'pattern' translated by 'shift'
    """
    shifted_pattern = [list(a) for a in zip(map(lambda x: shift[0] + x, zip(*pattern)[0]), map(lambda y: shift[1] + y, zip(*pattern)[1]))]
    return shifted_pattern

class CBRAHMSTestP1(TestCase):

    def setUp(self):
        # Over the Rainbow query
        self.pattern = [[0,48],[4,60],[8,59],[10,55],[11,57],[12,59],[14,60]]
        self.lemstrom_source = 'music_files/lemstrom2011_test/leiermann.mid'
        # A function to return a query file name. Usage: self.lemstrom_query('a') --> 'query_a.mid'
        self.lemstrom_query = lambda x: 'music_files/lemstrom2011_test/query_' + x + '.mid'

    def tearDown(self):
        pass

    def test_shift_pattern(self):
        shift = [1,1]
        source = shift_pattern(shift, self.pattern)
        expected = [[1,49],[5,61],[9,60],[11,56],[12,58],[13,60],[15,61]]
        self.assertEqual(source, expected)

    def test_P1_edgecase_same_size_transposed(self):
        """
        Checks if P1 can match a pattern to a source of the same size, but transposed.
        """
        # transpose pattern 12 semitones upwards
        shift = [0,12]
        source = shift_pattern(shift, self.pattern)
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
            source.extend(shift_pattern(expected_matches[i], self.pattern))

        list_of_shifts = cbrahmsGeo.P1(self.pattern, source)
        self.assertEqual(list_of_shifts, expected_matches)


    def test_P1_midiparser_lemstrom(self):
        """
        Parses the ground truth polyphonic music example provided in Lemstrom and Laitninen's 2011 paper. There should be only one exact occurrence found by P1. 
        """
        parsed_source = midiparser.run(self.lemstrom_source)
        parsed_pattern = midiparser.run(self.lemstrom_query('a'))
        list_of_shifts = cbrahmsGeo.P1(parsed_pattern, parsed_source)
        self.assertEqual(list_of_shifts, [[3.0, 2]])

    def test_P1_midiparser_chidori(self):
        """
        Parses the Chidori Meimei Japanese folk song and searches for all four occurrences of a common four-note motif
        """
        chidori_source = 'music_files/chidori_meimei.mid'
        chidori_pattern = 'music_files/chidori_query.mid'
        parsed_source = midiparser.run(chidori_source)
        parsed_pattern = midiparser.run(chidori_pattern)
        list_of_shifts = cbrahmsGeo.P1(parsed_pattern, parsed_source)
        self.assertEqual(list_of_shifts, [[2.0, -10], [6.0, -10], [65.0, -10], [69.0, -10]])


CBRAHMSTestP1_SUITE = TestLoader().loadTestsFromTestCase(CBRAHMSTestP1)

