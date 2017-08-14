import path
import music21
import unittest
import patternfinder.geometric_helsinki as geometric_helsinki

from parameterized import parameterized
from tests.custom_assertions import CustomAssertions

class TestExactMatches(unittest.TestCase, CustomAssertions):

    def setUp(self):
        pass

    @parameterized.expand([
        ((offset, transpose), settings)
                for transpose in 'P1 d2 m2 M2 A2 d3 m3 M3 A3 P4 A4 D5 P5 A5 m6 M6 A6 d7 m7 M7 A7 P8'.split(' ')
                for offset in (range(0, 15, 7))
                for settings in (
                    {
                        'algorithm' : algy,
                        'threshold' : 'all',
                        'pattern_window' : 1,
                        'source_window' : 1} for algy in 'P1 S1 S2 W1 W2'.split(' '))
                ])
    def test_edgecase_geometric_helsinki_identical_source_shifted_by(self, shift, settings):
        """ Source is a shifted copy of the pattern"""
        offset, pitch = shift
        pattern = music21.converter.parse('tests/data/ely_lullaby.xml').measures(1,4)

        # stream.transpose() returns a new stream (or at least, it should...)
        source = pattern.transpose(pitch)
        source.shiftElements(offset)

        # Get a generator
        my_finder = geometric_helsinki.Finder(pattern, source, **settings)

        # Assert that the first and only occurrence is made up of the shifted source 
        self.assertEqual(next(my_finder).notes, list(source.flat.notes))
        self.assertRaises(StopIteration, lambda: next(my_finder))

    """
    @parameterized.expand(algorithms.items())
    @skip # TODO all algorithms fail this test. What is the desired behaviour? One or two occurrences?
    def test_edgecase_source_has_superimposed_note(self, _, algorithm):
        If the pattern occurs in a source, and within that passage the source has a subset of notes which are duplicated (for example, if the trumpet doubles the clarinet only on the down beats), then the algorithm should find a multiplicity of translations. How many, though? This is instead of the naive behavior, which would find just one occurrence.
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
        Similar test to above, with the entire pattern duplicated instead of just one note
        self.source.extend(self.source)
        expected_matches = [TwoDVector(0,0), TwoDVector(0,0)]

        list_of_shifts = algorithm(self.pattern, self.source)
        self.assertEqual(list_of_shifts, expected_matches)

    @parameterized.expand(algorithms.items())
    # TODO P2 fails this test, but again is a result of its behaviour. This would make sense, since the translation multiplicity will be double what is expected.
    @skip # Desired behaviour?
    def test_edgecase_pattern_is_duplicated_source_is_pattern(self, _, algorithm):
        Given a source, identical to the pattern, this test tries to find an occurrence of a doubled pattern in the source. For example, if the clarinet and trumpet played in unison, can you find the doubled pattern in the piano reduction, which just has one occurrence of the pattern?
        The expected behaviour should be NO, the algorithm will not find this occurrence, since a doubled pattern should only match exactly with a doubled source.
        self.pattern.extend(self.pattern)
        expected_matches = []
        list_of_shifts = algorithm(self.pattern, self.source)
        self.assertEqual(list_of_shifts, expected_matches)

    @parameterized.expand(algorithms.items())
    def test_source_is_repeated_pattern(self, _, algorithm):
        Creates a source which consists of many pattern repetitions, each being transposed slightly. Then tests whether the algorithm can find each sequential occurrence of the pattern.
        num_repetitions = 30
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
        source = [LineSegment(*d) for d in ((0,2,48), (2,2,48), (4,2,60), (6,2,60), (8,1,59), (9,1,59), (10,0.5,55), (10.5,0.5,55), (11,0.5,57), (11.5,0.5,57), (12,1,59), (13, 1, 59), (14,1,60), (15,1,60))]
        expected_matches = [TwoDVector(0,0)]
        list_of_shifts = cbrahmsGeo.P3(self.pattern, self.source)
        self.assertEqual(list_of_shifts, expected_matches)


    @parameterized.expand(algorithms.items())
    def test_midiparser_chidori(self, _, algorithm):
        Parses the Chidori Meimei Japanese folk song and searches for all four occurrences of a common four-note motif
        list_of_shifts = tools.run_algorithm_with_midiparser(algorithm, 'music_files/chidori_query.mid', 'music_files/chidori_meimei.mid')
        self.assertEqual(list_of_shifts, [TwoDVector(d[0], d[1]) for d in [[2.0, -10], [6.0, -10], [65.0, -10], [69.0, -10]]])

    @parameterized.expand(algorithms.items())
    def test_midiparser_bwv2(self, _, algorithm):
        Parses Bach's BWV2 chorale and searches for a V-i cadence query
        list_of_shifts = tools.run_algorithm_with_midiparser(algorithm, 'music_files/query_V-i.mid', 'music_files/bach_BWV2_chorale.krn')
        self.assertEqual(list_of_shifts, [TwoDVector(30.0, 0)])

    """

exact_matches_suite = unittest.TestLoader().loadTestsFromTestCase(TestExactMatches)

if __name__ == '__main__':
    exact_matches_suite.debug()
