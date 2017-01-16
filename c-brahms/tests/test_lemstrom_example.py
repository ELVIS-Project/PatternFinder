from unittest import TestCase, TestLoader
from tests import tools
from functools import partial
from nose_parameterized import parameterized
from LineSegment import TwoDVector
import cbrahmsGeo
import midiparser
import pdb


class TestLemstromExample(TestCase):

    def setUp(self):
        self.lemstrom_source = 'music_files/lemstrom2011_test/leiermann.mid'
        # A function to return a query file name. Usage: self.lemstrom_query('a') --> 'query_a.mid'
        self.lemstrom_query = lambda x: 'music_files/lemstrom2011_test/query_' + x + '.mid'

    def tearDown(self):
        pass

    @parameterized.expand([
        ("P1_onset", partial(cbrahmsGeo.P1, option = 'onset')),
        ("P1_segment", partial(cbrahmsGeo.P1, option = 'segment')),
        ("P2", partial(cbrahmsGeo.P2, option = 0)),
        ("P3", partial(cbrahmsGeo.P3, option = 0))
    ])
    def test_P1_midiparser_lemstrom_example(self, _, algorithm):
        """
        EXACT MATCH Query A
        Parses the ground truth polyphonic music example provided in Lemstrom and Laitninen's 2011 paper. Query A is an exact occurrence, and should be found by all algorithms if their error tolerance is zero.
        """
        list_of_shifts = tools.run_algorithm_with_midiparser(algorithm, self.lemstrom_query('a'), self.lemstrom_source)
        self.assertEqual(list_of_shifts, [TwoDVector(3.0, 2)])

    def test_P2_midiparser_lemstrom_example(self):
        """
        ONE MISMATCH Query B Algorithm P2
        Parses the ground truth polyphonic music example provided in Lemstrom and Laitninen's 2011 paper. It should be able to find query B with option = 1 mismatch.
        """
        algorithm = partial(cbrahmsGeo.P2, option = 1)
        one_mismatch = tools.run_algorithm_with_midiparser(algorithm, self.lemstrom_query('b'), self.lemstrom_source)
        self.assertEqual(one_mismatch, [TwoDVector(3.0, 2)])

LEMSTROM_EXAMPLE_SUITE = TestLoader().loadTestsFromTestCase(TestLemstromExample)
