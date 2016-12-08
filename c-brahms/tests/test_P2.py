from unittest import TestCase, TestLoader
from functools import partial
import random
from vis.analyzers.indexers import noterest, metre
from tests import tools
from LineSegment import LineSegment, TwoDVector
import cbrahmsGeo
import midiparser
import music21
import pandas
import pdb
import copy

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
        return TwoDVector(0, random.randint(low, high))

    # Get a random sample without replacement of size #num_mismatch
    modified_notes = random.sample(counted_notes, num_mismatches)
    # Transpose notes that are in the sample. Enumeration is required, otherwise we might transpose duplicate notes more times than their multiplicity in the sample.
    return [n + random_shift(-24, 24) if (i, n) in modified_notes else n for i, n in counted_notes]

class CBRAHMSTestP2(TestCase):
    #TODO bug: P2 stalls infinitely if given an empty pattern.

    def setUp(self):
        # Over the Rainbow query
        self.pattern = [LineSegment(d) for d in [[0,4,48],[4,4,60],[8,2,59],[10,1,55],[11,1,57],[12,2,59],[14,2,60]]]
        # Identical source
        self.source = copy.deepcopy(self.pattern)

    def test_create_random_mismatches(self):
        """
        Tests an internally used function create_random_mismatches
        Creates a random number of mismatches in a pattern, then compares the original and the modified lists to ensure there is the expected number of mismatches.
        """
        num_mismatches = random.randint(1,len(self.pattern))
        modified_pattern = create_random_mismatches(self.pattern, num_mismatches)

        actual_mismatches = count_mismatches(modified_pattern, self.source)
        self.assertEqual(actual_mismatches, num_mismatches)

    def test_edgecase_one_random_mismatch_same_size(self):
        source = copy.deepcopy(self.pattern)

        pattern = create_random_mismatches(self.pattern, 1)
        list_of_shifts = cbrahmsGeo.P2(pattern, source, 1)
        self.assertEqual(list_of_shifts, [TwoDVector(0,0)])

        # Same test with the source transposed
        shift = TwoDVector(0, 5)
        source = [s + shift for s in source]
        list_of_shifts = cbrahmsGeo.P2(pattern, source, 1)
        self.assertEqual(list_of_shifts, [shift])

    def test_edgecase_all_no_similarity(self):
        """
        Tests whether P2 "all" option will return exactly len(pattern) * len(source) shifts when the pattern and source share no similarity whatsoever
        """
        source = [LineSegment([p.onset, p.duration, p.pitch * (p.onset + 100)]) for p in self.pattern] # Assumes no interval is greater than 100 semitones
        list_of_shifts = cbrahmsGeo.P2(self.pattern, source, "all")
        self.assertEqual(len(list_of_shifts), len(self.pattern) * len(source))

    def test_edgecase_duplicate_melody_random_mismatch(self):
        num_mismatches = random.randrange(1, 2)
        source = copy.deepcopy(self.pattern)

        modified_source = create_random_mismatches(source, 1)
        modified_source.extend(source)
        expected_matches = [TwoDVector(0,0), TwoDVector(0,0)]

        list_of_shifts = cbrahmsGeo.P2(self.pattern, source, 0)
        self.assertEqual(list_of_shifts, expected_matches)

    def test_repeated_pattern_in_source_random_mismatch(self):
        num_repetitions = 3
        num_mismatches = random.randrange(1, 2)

        source = create_random_mismatches(copy.deepcopy(self.pattern), num_mismatches)
        expected_matches = [TwoDVector(0, 0)]

        # Repeat the pattern by adding a new occurrence on to the end
        for i in range(1, num_repetitions):
            # Attach new occurrences such that there is no overlap
            new_start_onset = source[-1].onset + source[-1].duration + max([p.duration for p in self.pattern])
            # Transpose pattern occurrences up to two octaves
            expected_matches.append(TwoDVector(new_start_onset, i % 24))
            # Create random mismatches
            modified_pattern = create_random_mismatches([p + expected_matches[i] for p in self.pattern], num_mismatches)
            # Append to source
            source.extend(modified_pattern)

        list_of_shifts = cbrahmsGeo.P2(self.pattern, source, num_mismatches)
        self.assertEqual(list_of_shifts, expected_matches)


P2_SUITE = TestLoader().loadTestsFromTestCase(CBRAHMSTestP2)
