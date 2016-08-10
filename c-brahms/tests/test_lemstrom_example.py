from unittest import TestCase, TestLoader
from tests import tools
from functools import partial
import cbrahmsGeo
import midiparser
import pdb


class CBRAHMSTestLemstromExample(TestCase):

    def setUp(self):
        self.lemstrom_source = 'music_files/lemstrom2011_test/leiermann.mid'
        # A function to return a query file name. Usage: self.lemstrom_query('a') --> 'query_a.mid'
        self.lemstrom_query = lambda x: 'music_files/lemstrom2011_test/query_' + x + '.mid'

    def tearDown(self):
        pass

    def test_P1_midiparser_lemstrom_example(self):
        """
        Parses the ground truth polyphonic music example provided in Lemstrom and Laitninen's 2011 paper. Query A is an exact occurrence, and should be found by algorithm P1.
        """
        list_of_shifts = tools.run_algorithm_with_midiparser(cbrahmsGeo.P1, self.lemstrom_query('a'), self.lemstrom_source)
        self.assertEqual(list_of_shifts, [[3.0, 2]])

    def test_P2_midiparser_lemstrom_example(self):
        """
        Parses the ground truth polyphonic music example provided in Lemstrom and Laitninen's 2011 paper. Depending on its error tolerance, P2 should be able to find query A (i.e., P2 with mismatch = 0 should behave identically to P1). Additionally, it should be able to find query B, which has 1 mismatch.
        """
        exact_matches = tools.run_algorithm_with_midiparser(partial(cbrahmsGeo.P2, mismatch = 0), self.lemstrom_query('a'), self.lemstrom_source)
        self.assertEqual(exact_matches, [[3.0, 2]])
        one_mismatch = tools.run_algorithm_with_midiparser(partial(cbrahmsGeo.P2, mismatch = 1), self.lemstrom_query('b'), self.lemstrom_source)
        self.assertEqual(one_mismatch, [[3.0, 2]])

LEMSTROM_EXAMPLE_SUITE = TestLoader().loadTestsFromTestCase(CBRAHMSTestLemstromExample)
