from unittest import TestCase, TestLoader, TestSuite # test framework
from nose_parameterized import parameterized, param # for auto-generating tests
from vis.analyzers.indexers import noterest, metre # vis
import music21
import pandas
from tests import tools # parsing tools
from functools import partial # to force exact matching on all algorithms
from LineSegment import TwoDVector, LineSegment # data structures
import copy
import cbrahmsGeo
import midiparser
import pdb
import nose


class TestPangeLingua(TestCase):

    # Datapaths
    music_folder = "music_files/pange_lingua/"
    source_path = music_folder + "pange_lingua.xml"

    # Index the source for the whole class to avoid unnecessary re-indexing for each test case
    indexed_source = tools.index_source_from_score(source_path)

    exact_algorithms=[
        ("P1-onset", partial(cbrahmsGeo.P1, option='onset')),
        ("P1-segment", partial(cbrahmsGeo.P1, option='segment')),
        ("P2", partial(cbrahmsGeo.P2, option=0)),
        ("P3", partial(cbrahmsGeo.P3, option=0))
    ]

    # List of queries. To add new tests - format is ("query_filename", [list of algorithms tuples e.g. ("algy-name", function) to test this query], [expected results])
    QUERIES = [
            # Tenor entry in measure 1. Repeats exactly in the Soprano at downbeat of m.5
            ("kyrie1_tenor_mm1-4.xml", exact_algorithms, [[0, -12], [48, 0]]),
            # Bass entry in measure 2. Repeats with 2 mismatch in the Alto at downbeat of m.6
            ("kyrie1_bass_mm2-5.xml", exact_algorithms, [[12, 0]]),
            ("kyrie1_bass_mm2-5.xml", [("P2-option2", partial(cbrahmsGeo.P2, option=2))], [[60, 12]])
    ]

    TESTS = reduce(lambda x, y: x+y, [[{
            'query' : music_folder + q,
            'algorithm' : algy,
            'expected' : e
        } for algy in a] for (q, a, e) in QUERIES])

    def custom_func_name(testcase_func, param_num, param):
        return "%s_algorithm_%s_%s" % (
                testcase_func.__name__,
                param[1]['algorithm'][0], #algorithm[0] for string name
                param[1]['query']
        )

    @parameterized.expand([param(**case) for case in TESTS], testcase_func_name = custom_func_name)
    def test_pange_lingua(self, query, algorithm, expected, source=source_path):
        indexed_pattern = tools.index_pattern_from_score(query)
        list_of_shifts = tools.run_algorithm_with_indexed_pieces(algorithm[1], indexed_pattern, TestPangeLingua.indexed_source) #algorithm[1] for function pointer
        self.assertEqual(list_of_shifts, [TwoDVector(d[0], d[1]) for d in expected])

PANGE_LINGUA_SUITE = TestLoader().loadTestsFromTestCase(TestPangeLingua)
