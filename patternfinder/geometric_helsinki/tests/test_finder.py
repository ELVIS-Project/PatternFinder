import music21
import pdb

from unittest import TestCase, TestLoader, TestSuite, TextTestRunner # test framework
from patternfinder.geometric_helsinki.tests.test_lemstrom_example import LEM_PATH_PATTERN, LEM_PATH_SOURCE
from patternfinder.geometric_helsinki import Finder
from patternfinder.geometric_helsinki.NoteSegment import NotePointSet, InterNoteVector


class TestFinder(TestCase):

    def test_NotePointSet(self):
        score = music21.converter.parse(LEM_PATH_SOURCE)
        point_set = NotePointSet(score)

    def test_scale(self):
        p = music21.converter.parse('tinynotation: 4/4 c4 e4 g4')
        s = music21.converter.parse('tinynotation: 4/4 c4 e4 g4 c2 e2 g2')

        foo = Finder(p, s, scale=2.0)
        occ = next(foo)
        self.assertEqual(occ, [InterNoteVector(
            foo.patternPointSet[p_i], foo.patternPointSet,
            foo.sourcePointSet[s_i], foo.sourcePointSet)
            for p_i, s_i in ((0, 3), (1, 4), (2, 5))])

finder_suite = TestLoader().loadTestsFromTestCase(TestFinder)

if __name__ == "__main__":
    result = TextTestRunner(verbosity=2).run(finder_suite)
