from unittest import TestCase, TestLoader, expectedFailure, skip
from functools import partial
import random
from vis.analyzers.indexers import noterest, metre
from tests import tools
from LineSegment import LineSegment, TwoDVector
import cbrahmsGeo
import midiparser
import music21
import pandas
import copy
import pdb

def count_mismatches(pattern, source):
    """
    For internal use by class CBRAHMSTestP2
    Counts the number of note mismatches between pattern and source.
    """
    return len([p for p in pattern if p not in source])

def create_random_mismatches(pattern, num_mismatches):
    """
    For internal use by class CBRAHMSTestP2.
    Selects a random subset of notes in the pattern and transposes them. (the desired transposition is separately generated for each note)
    Returns a new list; leaves the argument unchanged.
    """
    counted_notes = list(enumerate(pattern))

    def random_shift(low, high):
        # range(5, -1) and range (1, -5) return []
        numbers = range(low, -1) + range(1, high) # Can't allow 0 since we need to create an expected number of mismatches
        return TwoDVector(0, random.choice(numbers))

    # Get a random sample without replacement of size #num_mismatch
    modified_notes = random.sample(counted_notes, num_mismatches)
    # Transpose notes that are in the sample. Enumeration is required, otherwise we might transpose duplicate notes more times than their multiplicity in the sample.
    return [n + random_shift(-24, 24) if (i, n) in modified_notes else n for i, n in counted_notes]

class TestP2(TestCase):
    #TODO bug: P2 stalls infinitely if given an empty pattern.
    #TODO instead of testing random mismatches, test all possible ones

    def setUp(self):
        # Over the Rainbow query
        self.pattern = [LineSegment(*d) for d in [(0,4,48),(4,4,60),(8,2,59),(10,1,55),(11,1,57),(12,2,59),(14,2,60)]]
        # Identical source
        self.source = copy.deepcopy(self.pattern)

    def test_function_create_random_mismatches(self):
        """
        Tests an internally used function create_random_mismatches
        Creates a random number of mismatches in a pattern, then compares the original and the modified lists to ensure there is the expected number of mismatches.
        """
        for n in range(1, len(self.pattern)):
            modified_pattern = create_random_mismatches(self.pattern, n)
            actual_mismatches = count_mismatches(modified_pattern, self.source)
            self.longMessage = True
            self.assertEqual(actual_mismatches, n, msg='\n modified_pattern {0} \n modified source {1}'.format(modified_pattern, self.source))

    def test_edgecase_one_to_n_random_mismatches_source_same_size(self):
        """
        Starts with an identical pattern and source. Then tests that P2 can find the (0,0) translation after modifying the pattern with 1-len(pattern) mismatches
        """
        for n in range(1, len(self.pattern)):
            modified_pattern = create_random_mismatches(self.pattern, n)
            list_of_shifts = cbrahmsGeo.P2(modified_pattern, self.source, n)
            self.assertIn(TwoDVector(0,0), list_of_shifts)

    @expectedFailure
    def test_edgecase_one_to_n_random_mismatches_source_is_repeated_pattern(self):
        """
        Creates a source which consists of many pattern repetitions, each being transposed and slightly modified with pitch mismatches.
        Tests whether P2 can find each sequential occurrence of the pattern, given the correct mismatch.
        """
        # TODO Very weird bug.
        # try:
        # step into create_random_mismatches()
        # pp counted_notes
        # pp modified_notes
        # pp [n + random_shift(-24,24) if (i, n) in modified_notes else n for i, n in counted_notes]
        # pp LineSegment() + random_shift
        # -----
        # The mismatched note always gets the onset of the first repetition. So odd, since the addition works fine on its own. Ugh.
        #pdb.set_trace()

        num_repetitions = 10
        num_mismatches = random.randrange(1, 2)
        max_rest_in_pattern = max([j.x - i.x for i, j in zip(self.pattern[:-1], self.pattern[1:])]) + 1

        source = create_random_mismatches(self.source, num_mismatches)
        expected_matches = [TwoDVector(0, 0)]

        # Repeat the pattern by adding a new occurrence on to the end
        for i in range(1, num_repetitions):
            # Attach new occurrences such that the rest between occurrences is bigger than any rest in the pattern
            new_start_onset = source[-1].onset + source[-1].duration + max_rest_in_pattern
            # Transpose pattern occurrences up to two octaves
            expected_matches.append(TwoDVector(new_start_onset, i % 24))
            transposed_pattern = [p + expected_matches[i] for p in self.pattern]
            # Create random mismatches
            modified_pattern = create_random_mismatches(transposed_pattern, num_mismatches)
            # Append to source
            source.extend(modified_pattern)

        list_of_shifts = cbrahmsGeo.P2(self.pattern, source, num_mismatches)
        self.assertEqual(list_of_shifts, expected_matches)

    @skip
    def test_edgecase_option_all_source_no_similarity(self):
        """
        Tests whether P2 "all" option will return exactly len(pattern) * len(source) shifts when the pattern and source share no similarity whatsoever
        """
        source = [LineSegment(p.onset, p.pitch * (p.onset + 100), p.duration) for p in self.pattern] # Assumes no interval is greater than 100 semitones
        list_of_shifts = cbrahmsGeo.P2(self.pattern, source, "all")
        self.assertEqual(len(list_of_shifts), len(self.pattern) * len(source))

    @expectedFailure # TODO Requires change in P2 behavior. Since P2 relies on counting translation multiplicity, this test currently fails. The two unison occurrences result in a translation multiplicity two times the normal magnitude.
    def test_edgecase_one_mismatch_source_is_two_superimposed_patterns(self):
        """
        Given a source with two unison occurrences of the same pattern, test that P2 can find two identical translations.
        Also puts a random mismatch in the copy.
        """
        num_mismatches = 1

        modified_source = create_random_mismatches(self.source, 1)
        modified_source.extend(self.source)
        expected_matches = [TwoDVector(0,0), TwoDVector(0,0)]

        list_of_shifts = cbrahmsGeo.P2(self.pattern, source, 0)
        self.assertEqual(list_of_shifts, expected_matches)


P2_SUITE = TestLoader().loadTestsFromTestCase(TestP2)
