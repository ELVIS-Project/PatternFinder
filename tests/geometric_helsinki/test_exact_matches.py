import music21
import unittest
import patternfinder.geometric_helsinki as geometric_helsinki
import pdb

from pprint import pformat # test fail messages 
from parameterized import parameterized
from tests.custom_assertions import CustomAssertions

INTERVALS_UNDER_AN_OCTAVE = 'P1 d2 m2 M2 A2 d3 m3 M3 A3 P4 A4 D5 P5 A5 m6 M6 A6 d7 m7 M7 A7 P8'

class TestExactMatches(unittest.TestCase, CustomAssertions):

    def setUp(self):
        pass

    def run(self, result=None):
        """
        Stop after first error

        Code source:
            Kevin Sookocheff
            <https://sookocheff.com/post/python/halting-unittest-execution-at-first-error/>
        """
        if not result.errors:
            super(TestExactMatches, self).run(result)

    @parameterized.expand([
        ((offset, transpose), settings)
                for transpose in INTERVALS_UNDER_AN_OCTAVE.split(' ')
                for offset in (0, 7)
                for settings in (
                    {
                        'algorithm' : algy,
                        'threshold' : 'all',
                        'pattern_window' : 1,
                        'source_window' : 1} for algy in geometric_helsinki.implemented_algorithms)
                ])
    def test_geometric_helsinki_identical_source_shifted_by(self, shift, settings):
        """ Source is a shifted copy of the pattern"""
        offset, pitch = shift
        pattern = music21.converter.parse('tests/data/ely_lullaby.xml').measures(1,4)

        # stream.transpose() returns a new stream (or at least, it should...)
        source = pattern.transpose(pitch)
        source.shiftElements(offset)

        # Get a generator
        my_finder = geometric_helsinki.Finder(pattern, source, **settings)

        # Assert that the first and only occurrence is made up of the shifted source 
        found_occ = next(my_finder)
        self.assertEqual(found_occ.notes, list(source.flat.notes), msg =
                "\nFOUND \n{0}\n EXPECTED\n{1}".format(pformat(found_occ.notes), pformat(list(source.flat.notes))))
        self.assertRaises(StopIteration, lambda: next(my_finder))


    @parameterized.expand([
        ((offset, transpose), settings)
                for transpose in INTERVALS_UNDER_AN_OCTAVE.split(' ')
                for offset in (0, 7)
                for settings in (
                    {
                        'algorithm' : algy,
                        'threshold' : 'all',
                        'pattern_window' : 1,
                        'source_window' : 2} for algy in geometric_helsinki.implemented_algorithms)
                ])
    def test_geometric_helsinki_melodic_pattern_in_pedaled_and_chordified_source_shifted_by(self, shift, settings):
        """Source is a transposed copy of the pattern, with an additional pedal note"""
        offset, pitch = shift
        pattern = music21.converter.parse('tests/data/ely_lullaby.xml').measures(1,4)

        # stream.transpose() returns a new stream (or at least, it should...)
        # Convert each note into a chord
        source = pattern.transpose(pitch).chordify()
        source.shiftElements(offset)

        # Put a pedal in the bass at each offset
        for chord in source.flat.notes:
            chord.add('A2')

        # Get a generator
        my_finder = geometric_helsinki.Finder(pattern, source, **settings)

        # Assert that the first and only occurrence is made up of the shifted source 
        found_occ = next(my_finder)
        self.assertEqual(found_occ.notes, list(source.flat.notes), msg =
                "\nFOUND \n{0}\n EXPECTED\n{1}".format(pformat(found_occ.notes), pformat(list(source.flat.notes))))
        self.assertRaises(StopIteration, lambda: next(my_finder))


    #@TODO 
    #6)python find_matches.py P1 music_files/schubert_soggettos/casulana1.xml music_files/schubert_soggettos/Casulan2-4-2.xml  will find a match at offset 18, transposition 17, with intersection length of 8. meaning hte first note of the query (c in the bass) should match to a note 17 semitones above (bottom space f in treble) - but there is no F in measure 3 of the source!! UGH
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
    # If this test script is run from the command line, let errors propagate (use .debug())
    exact_matches_suite.debug()
