from unittest import TestCase, TestLoader, TestSuite
from nose_parameterized import parameterized, param
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


class TestPangeLingua(TestCase):

    P1 = partial(cbrahmsGeo.P1, option='onset')
    P2 = partial(cbrahmsGeo.P2, option=0)
    P3 = partial(cbrahmsGeo.P3, option=0)
    algorithms=[
        ("P1", P1),
        ("P2", P2),
        ("P3", P3)
    ]

    music_folder = "music_files/pange_lingua/"
    source_path = music_folder + "pange_lingua.xml"

    # Index the source for the whole class to avoid unnecessary re-indexing for each test case
    indexed_source = tools.index_source_from_score(source_path)

    TESTS = [
        # Tenor entry in measure 1. Repeats exactly in the Soprano at downbeat of m.5
        {
            'name' : "kyrie1.1_P1_tenor_entry",
            'algorithm' : P1,
            'query' : "music_files/pange_lingua/kyrie1.1_tenor1-4.xml",
            'expected' : [[0, -12], [48, 0]]},

        # Bass entry in measure 2. Repeats with 2 mismatch in the Alto at downbeat of m.6
        {
            'name' : "kyrie1.1_P2_bass_entry",
            'algorithm' : P1,
            'query' : music_folder + "kyrie1.1_bass2-5.xml",
            'expected' : [[12, 0]]},
        {
            'name' : "kyrie1.1_P2_bass_entry_alto_imitation",
            'algorithm' : partial(cbrahmsGeo.P2, option=2),
            'query' : music_folder + "kyrie1.1_bass2-5.xml",
            'expected' : [[60, 12]]}
        ]

    @parameterized.expand(param(**case) for case in TESTS)
    def test(self, name, algorithm, query, expected, source=source_path):
        indexed_pattern = tools.index_pattern_from_score(query)
        list_of_shifts = tools.run_algorithm_with_indexed_pieces(algorithm, indexed_pattern, TestPangeLingua.indexed_source)
        self.assertEqual(list_of_shifts, [TwoDVector(d[0], d[1]) for d in expected])

"""
        list_of_shifts = tools.run_algorithm_with_midiparser(algorithm, 'music_files/pange_lingua/kyrie1.1_tenor1-4.xml', 'music_files/pange_lingua/pange_lingua.xml')
        self.assertEqual(list_of_shifts, [TwoDVector(0, -12), TwoDVector(48, 0)])

        #find bass entry
        list_of_shifts = tools.run_algorithm_with_midiparser(algorithm, 'music_files/pange_lingua/kyrie1.1_bass2-5.xml', 'music_files/pange_lingua/pange_lingua.xml')
        self.assertEqual(list_of_shifts, [TwoDVector(12, 0)])

        #find bass entry 2 mismatch in alto entry
        list_of_shifts = tools.run_algorithm_with_midiparser(partial(cbrahmsGeo.P2, option=2), 'music_files/pange_lingua/kyrie1.1_bass2-5.xml', 'music_files/pange_lingua/pange_lingua.xml')
        self.assertEqual(list_of_shifts, [TwoDVector(12, 60)])

        """
PANGE_LINGUA_SUITE = TestLoader().loadTestsFromTestCase(TestPangeLingua)
