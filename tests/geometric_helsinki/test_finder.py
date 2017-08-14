import music21
import pdb
import unittest

from parameterized import parameterized
from pprint import pformat # for test fail error messages

from patternfinder.geometric_helsinki.tests.test_lemstrom_example import LEM_PATH_PATTERN, LEM_PATH_SOURCE
from patternfinder.geometric_helsinki.finder import Finder
from patternfinder.geometric_helsinki.GeometricNotes import NotePointSet, InterNoteVector


TESTS = [
        ('scale', '4/4 c4 e4 g4', '4/4 c4 e4 g4 c2 e2 g2',
            {
                'scale' : 2.0
                },
            [((0,3), (1,4), (2,5))]),
        ('interval_func_generic', '4/4 c4 e-4 g4', '4/4 c4 e4 g4 c4 e-4 g4',
            {
                'interval_func' : 'generic'
                },
            [((0,0), (1,1), (2,2)), ((0,3), (1,4), (2,5))]),
        ('interval_func_semitones', '4/4 c4 e-4 g4', '4/4 c4 e4 g4 c4 e-4 g4',
            {
                'interval_func' : 'semitones'
                },
            [((0,3), (1,4), (2,5))]),
        ('interval_func_base40', '4/4 c4 e-4 g4', '4/4 c4 e4 g4 c4 d#4 g4',
            {
                'interval_func' : 'base40'
                },
            [((0,3), (1,4), (2,5))])]

class TestFinder(unittest.TestCase):

    def setUp(self):
        self.longMessage = True

    def test_edgecase_empty(self):
        """Empty initialization of Finder should still work like an empty iterator"""
        my_finder = Finder()
        self.assertRaises(StopIteration, lambda: next(my_finder))

    def test_NotePointSet(self):
        melody = [music21.note.Note(pitch) for pitch in ('E4', 'F4', 'G4')]
        bass = [music21.note.Note(pitch) for pitch in ('C4', 'A3', 'E3')]
        score = music21.stream.Stream()

        for offset, m, b in zip(range(3), melody, bass):
            score.insertIntoNoteOrChord(offset, m)
            score.insertIntoNoteOrChord(offset, b)

        point_set = NotePointSet(score)

        for note, expected in zip(point_set, [note for tpl in zip(bass, melody) for note in tpl]):
            self.assertEqual(note, expected)

    @parameterized.expand(TESTS)
    def test_(self, name, pattern, source, settings, matching_pairs):
        p = music21.converter.parse('tinynotation: ' + pattern)
        s = music21.converter.parse('tinynotation: ' + source)

        my_finder = Finder(p, s, **settings)
        expected = [[InterNoteVector(
            my_finder.patternPointSet[p_i], my_finder.patternPointSet,
            my_finder.sourcePointSet[s_i], my_finder.sourcePointSet,
            y_func = my_finder.settings['interval_func'].algorithm)
            for p_i, s_i in occ] for occ in matching_pairs]
        occurrences = [occ.matching_pairs for occ in my_finder]

        if len(occurrences) != len(expected):
            self.fail("Not enough occurrences found"
                   + "\nExpected:\n" + pformat(expected)
                   + "\nFound:\n" + pformat(occurrences))
        for occurrence, exp in zip(occurrences, expected):
            self.assertEqual(occurrence, exp, msg =
                    "\nFOUND:\n" + pformat(occurrence) +
                    "\nEXPECTED\n" + pformat(exp))

finder_suite = unittest.TestLoader().loadTestsFromTestCase(TestFinder)

if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(finder_suite)
